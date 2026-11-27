package sqlite

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"gh-token-broker/internal/secretstore"
	_ "modernc.org/sqlite"
)

const RefreshTokenKind = "github-refresh-token"

type Store struct {
	db *sql.DB
	kp KeyProvider
}

var _ secretstore.Store = (*Store)(nil)

type Account struct {
	ID               string
	Host             string
	ClientID         string
	UserLogin        string
	AuthStatus       string
	RefreshSecretRef string
	ParentExpiresAt  time.Time
	RefreshExpiresAt time.Time
	LastRefreshAt    time.Time
	LastErrorCode    string
	CreatedAt        time.Time
	UpdatedAt        time.Time
}

func RefreshSecretRef(accountID string) string {
	return "account/" + accountID + "/refresh-token"
}

func Open(ctx context.Context, path string, kp KeyProvider) (*Store, error) {
	if kp == nil {
		return nil, errors.New("key provider is required")
	}
	if path != ":memory:" {
		if dir := filepath.Dir(path); dir != "." {
			if err := os.MkdirAll(dir, 0o700); err != nil {
				return nil, fmt.Errorf("create database directory: %w", err)
			}
		}
	}
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, fmt.Errorf("open sqlite: %w", err)
	}
	db.SetMaxOpenConns(1)
	store := &Store{db: db, kp: kp}
	if err := store.migrate(ctx); err != nil {
		db.Close()
		return nil, err
	}
	return store, nil
}

func (s *Store) Close() error {
	return s.db.Close()
}

func (s *Store) migrate(ctx context.Context) error {
	statements := []string{
		`CREATE TABLE IF NOT EXISTS secrets (
			ref TEXT PRIMARY KEY,
			kind TEXT NOT NULL,
			ciphertext BLOB NOT NULL,
			nonce BLOB NOT NULL,
			key_version INTEGER NOT NULL,
			created_at TEXT NOT NULL,
			updated_at TEXT NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS accounts (
			id TEXT PRIMARY KEY,
			host TEXT NOT NULL,
			client_id TEXT NOT NULL,
			user_login TEXT NOT NULL DEFAULT '',
			auth_status TEXT NOT NULL,
			refresh_secret_ref TEXT NOT NULL DEFAULT '',
			parent_expires_at TEXT NOT NULL DEFAULT '',
			refresh_expires_at TEXT NOT NULL DEFAULT '',
			last_refresh_at TEXT NOT NULL DEFAULT '',
			last_error_code TEXT NOT NULL DEFAULT '',
			created_at TEXT NOT NULL,
			updated_at TEXT NOT NULL
		)`,
	}
	for _, statement := range statements {
		if _, err := s.db.ExecContext(ctx, statement); err != nil {
			return fmt.Errorf("migrate sqlite: %w", err)
		}
	}
	return nil
}

func (s *Store) PutSecret(ctx context.Context, ref, kind string, plaintext []byte) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err := s.putSecretTx(ctx, tx, ref, kind, plaintext); err != nil {
		return err
	}
	return tx.Commit()
}

func (s *Store) putSecretTx(ctx context.Context, tx *sql.Tx, ref, kind string, plaintext []byte) error {
	if ref == "" || kind == "" {
		return errors.New("secret ref and kind are required")
	}
	if len(plaintext) == 0 {
		return errors.New("secret plaintext is empty")
	}
	masterKey, err := s.kp.MasterKey(ctx)
	if err != nil {
		return fmt.Errorf("load master key: %w", err)
	}
	defer zeroizeBytes(masterKey)
	aad := secretAssociatedData(ref, kind, keyVersion)
	ciphertext, nonce, err := encryptSecret(masterKey, plaintext, aad)
	if err != nil {
		return fmt.Errorf("encrypt secret: %w", err)
	}
	now := formatDBTime(time.Now())
	_, err = tx.ExecContext(ctx, `INSERT INTO secrets
		(ref, kind, ciphertext, nonce, key_version, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(ref) DO UPDATE SET
			kind=excluded.kind,
			ciphertext=excluded.ciphertext,
			nonce=excluded.nonce,
			key_version=excluded.key_version,
			updated_at=excluded.updated_at`,
		ref, kind, ciphertext, nonce, keyVersion, now, now)
	if err != nil {
		return fmt.Errorf("store encrypted secret: %w", err)
	}
	return nil
}

func (s *Store) GetSecret(ctx context.Context, ref string) ([]byte, error) {
	var kind string
	var ciphertext, nonce []byte
	var version int
	err := s.db.QueryRowContext(ctx, `SELECT kind, ciphertext, nonce, key_version FROM secrets WHERE ref = ?`, ref).
		Scan(&kind, &ciphertext, &nonce, &version)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, fmt.Errorf("secret %q not found", ref)
	}
	if err != nil {
		return nil, fmt.Errorf("read encrypted secret: %w", err)
	}
	masterKey, err := s.kp.MasterKey(ctx)
	if err != nil {
		return nil, fmt.Errorf("load master key: %w", err)
	}
	defer zeroizeBytes(masterKey)
	plaintext, err := decryptSecret(masterKey, ciphertext, nonce, secretAssociatedData(ref, kind, version))
	if err != nil {
		return nil, fmt.Errorf("decrypt secret %q: %w", ref, err)
	}
	return plaintext, nil
}

func (s *Store) SaveAuthorizedAccount(ctx context.Context, account Account, refreshToken []byte) error {
	if account.ID == "" || account.Host == "" || account.ClientID == "" {
		return errors.New("account id, host, and client id are required")
	}
	if len(refreshToken) == 0 {
		return errors.New("refresh token is required")
	}
	account.RefreshSecretRef = RefreshSecretRef(account.ID)
	now := time.Now().UTC()
	if account.CreatedAt.IsZero() {
		account.CreatedAt = now
	}
	account.UpdatedAt = now
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err := s.putSecretTx(ctx, tx, account.RefreshSecretRef, RefreshTokenKind, refreshToken); err != nil {
		return err
	}
	if err := upsertAccountTx(ctx, tx, account); err != nil {
		return err
	}
	return tx.Commit()
}

func (s *Store) RotateRefreshToken(ctx context.Context, accountID string, newRefreshToken []byte, parentExpiresAt, refreshExpiresAt time.Time, status, lastErrorCode string) error {
	if accountID == "" {
		return errors.New("account id is required")
	}
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if len(newRefreshToken) > 0 {
		if err := s.putSecretTx(ctx, tx, RefreshSecretRef(accountID), RefreshTokenKind, newRefreshToken); err != nil {
			return err
		}
	}
	now := formatDBTime(time.Now())
	result, err := tx.ExecContext(ctx, `UPDATE accounts SET
		auth_status = ?,
		refresh_secret_ref = ?,
		parent_expires_at = ?,
		refresh_expires_at = ?,
		last_refresh_at = ?,
		last_error_code = ?,
		updated_at = ?
		WHERE id = ?`,
		status, RefreshSecretRef(accountID), formatDBTime(parentExpiresAt), formatDBTime(refreshExpiresAt), now, lastErrorCode, now, accountID)
	if err != nil {
		return fmt.Errorf("update refresh chain state: %w", err)
	}
	rows, err := result.RowsAffected()
	if err == nil && rows == 0 {
		return fmt.Errorf("account %q not found", accountID)
	}
	return tx.Commit()
}

func (s *Store) UpdateAccountState(ctx context.Context, accountID, status, lastErrorCode string) error {
	now := formatDBTime(time.Now())
	result, err := s.db.ExecContext(ctx, `UPDATE accounts SET auth_status = ?, last_error_code = ?, updated_at = ? WHERE id = ?`, status, lastErrorCode, now, accountID)
	if err != nil {
		return fmt.Errorf("update account state: %w", err)
	}
	rows, err := result.RowsAffected()
	if err == nil && rows == 0 {
		return fmt.Errorf("account %q not found", accountID)
	}
	return nil
}

func upsertAccountTx(ctx context.Context, tx *sql.Tx, account Account) error {
	_, err := tx.ExecContext(ctx, `INSERT INTO accounts
		(id, host, client_id, user_login, auth_status, refresh_secret_ref, parent_expires_at, refresh_expires_at, last_refresh_at, last_error_code, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(id) DO UPDATE SET
			host=excluded.host,
			client_id=excluded.client_id,
			user_login=excluded.user_login,
			auth_status=excluded.auth_status,
			refresh_secret_ref=excluded.refresh_secret_ref,
			parent_expires_at=excluded.parent_expires_at,
			refresh_expires_at=excluded.refresh_expires_at,
			last_refresh_at=excluded.last_refresh_at,
			last_error_code=excluded.last_error_code,
			updated_at=excluded.updated_at`,
		account.ID,
		account.Host,
		account.ClientID,
		account.UserLogin,
		account.AuthStatus,
		account.RefreshSecretRef,
		formatDBTime(account.ParentExpiresAt),
		formatDBTime(account.RefreshExpiresAt),
		formatDBTime(account.LastRefreshAt),
		account.LastErrorCode,
		formatDBTime(account.CreatedAt),
		formatDBTime(account.UpdatedAt),
	)
	if err != nil {
		return fmt.Errorf("upsert account: %w", err)
	}
	return nil
}

func (s *Store) GetAccount(ctx context.Context, id string) (Account, error) {
	var account Account
	var parentExpires, refreshExpires, lastRefresh, created, updated string
	err := s.db.QueryRowContext(ctx, `SELECT id, host, client_id, user_login, auth_status, refresh_secret_ref,
		parent_expires_at, refresh_expires_at, last_refresh_at, last_error_code, created_at, updated_at
		FROM accounts WHERE id = ?`, id).Scan(
		&account.ID,
		&account.Host,
		&account.ClientID,
		&account.UserLogin,
		&account.AuthStatus,
		&account.RefreshSecretRef,
		&parentExpires,
		&refreshExpires,
		&lastRefresh,
		&account.LastErrorCode,
		&created,
		&updated,
	)
	if errors.Is(err, sql.ErrNoRows) {
		return Account{}, fmt.Errorf("account %q not found", id)
	}
	if err != nil {
		return Account{}, fmt.Errorf("read account: %w", err)
	}
	parsers := []struct {
		value string
		out   *time.Time
	}{
		{parentExpires, &account.ParentExpiresAt},
		{refreshExpires, &account.RefreshExpiresAt},
		{lastRefresh, &account.LastRefreshAt},
		{created, &account.CreatedAt},
		{updated, &account.UpdatedAt},
	}
	for _, parser := range parsers {
		if parser.value == "" {
			continue
		}
		parsed, err := time.Parse(time.RFC3339Nano, parser.value)
		if err != nil {
			return Account{}, fmt.Errorf("parse account timestamp: %w", err)
		}
		*parser.out = parsed
	}
	return account, nil
}

func formatDBTime(t time.Time) string {
	if t.IsZero() {
		return ""
	}
	return t.UTC().Format(time.RFC3339Nano)
}
