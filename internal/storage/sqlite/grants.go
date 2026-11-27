package sqlite

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"
)

const (
	GrantStatusActive   = "active"
	GrantStatusRedeemed = "redeemed"
	GrantStatusExpired  = "expired"
	GrantStatusRevoked  = "revoked"
)

var (
	ErrGrantNotFound   = errors.New("grant not found")
	ErrGrantNotUsable  = errors.New("grant is not usable")
	ErrGrantExhausted  = errors.New("grant use limit reached")
	ErrGrantExpired    = errors.New("grant expired")
	ErrAuditEventEmpty = errors.New("audit event type is required")
)

type Grant struct {
	GrantHash    string
	AgentID      string
	AccountID    string
	Host         string
	Owner        string
	Repo         string
	Profile      string
	MinTTL       time.Duration
	ExpiresAt    time.Time
	MaxUses      int
	UseCount     int
	Status       string
	CreatedAt    time.Time
	RedeemedAt   time.Time
	RevokedAt    time.Time
	RevokeReason string
}

type TokenIssue struct {
	ID                  string
	GrantHash           string
	AccountID           string
	TokenHash           string
	ExpiresAt           time.Time
	PermissionsJSON     string
	RepositorySelection string
	IssuedAt            time.Time
	RevokedAt           time.Time
	RevokeReason        string
}

type AuditEvent struct {
	ID           int64
	Timestamp    time.Time
	EventType    string
	ActorType    string
	ActorID      string
	SubjectType  string
	SubjectID    string
	Outcome      string
	Code         string
	MetadataJSON string
}

func (s *Store) CreateGrant(ctx context.Context, grant Grant) error {
	if grant.GrantHash == "" || grant.AgentID == "" || grant.AccountID == "" || grant.Host == "" || grant.Owner == "" || grant.Repo == "" || grant.Profile == "" {
		return errors.New("grant hash, agent id, account id, host, owner, repo, and profile are required")
	}
	if grant.MinTTL < time.Second {
		return errors.New("grant min_ttl must be at least one second")
	}
	if grant.MaxUses <= 0 {
		return errors.New("grant max_uses must be positive")
	}
	if grant.ExpiresAt.IsZero() {
		return errors.New("grant expires_at is required")
	}
	if grant.Status == "" {
		grant.Status = GrantStatusActive
	}
	if grant.Status != GrantStatusActive {
		return fmt.Errorf("new grant must start as %q", GrantStatusActive)
	}
	if grant.CreatedAt.IsZero() {
		grant.CreatedAt = time.Now().UTC()
	}
	_, err := s.db.ExecContext(ctx, `INSERT INTO grants
		(grant_hash, agent_id, account_id, host, owner, repo, profile, min_ttl_seconds, expires_at, max_uses, use_count, status, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)`,
		grant.GrantHash,
		grant.AgentID,
		grant.AccountID,
		grant.Host,
		grant.Owner,
		grant.Repo,
		grant.Profile,
		int64(grant.MinTTL/time.Second),
		formatDBTime(grant.ExpiresAt),
		grant.MaxUses,
		grant.Status,
		formatDBTime(grant.CreatedAt),
	)
	if err != nil {
		return fmt.Errorf("create grant: %w", err)
	}
	return nil
}

func (s *Store) GetGrant(ctx context.Context, grantHash string) (Grant, error) {
	var grant Grant
	var expiresAt, createdAt, redeemedAt, revokedAt string
	var minTTLSeconds int64
	err := s.db.QueryRowContext(ctx, `SELECT grant_hash, agent_id, account_id, host, owner, repo, profile,
		min_ttl_seconds, expires_at, max_uses, use_count, status, created_at, redeemed_at, revoked_at, revoke_reason
		FROM grants WHERE grant_hash = ?`, grantHash).Scan(
		&grant.GrantHash,
		&grant.AgentID,
		&grant.AccountID,
		&grant.Host,
		&grant.Owner,
		&grant.Repo,
		&grant.Profile,
		&minTTLSeconds,
		&expiresAt,
		&grant.MaxUses,
		&grant.UseCount,
		&grant.Status,
		&createdAt,
		&redeemedAt,
		&revokedAt,
		&grant.RevokeReason,
	)
	if errors.Is(err, sql.ErrNoRows) {
		return Grant{}, ErrGrantNotFound
	}
	if err != nil {
		return Grant{}, fmt.Errorf("read grant: %w", err)
	}
	grant.MinTTL = time.Duration(minTTLSeconds) * time.Second
	if err := parseGrantTimes(&grant, expiresAt, createdAt, redeemedAt, revokedAt); err != nil {
		return Grant{}, err
	}
	return grant, nil
}

func (s *Store) RedeemGrant(ctx context.Context, grantHash string, at time.Time) (Grant, error) {
	if at.IsZero() {
		at = time.Now().UTC()
	}
	result, err := s.db.ExecContext(ctx, `UPDATE grants SET
		use_count = use_count + 1,
		status = CASE WHEN use_count + 1 >= max_uses THEN ? ELSE status END,
		redeemed_at = ?
		WHERE grant_hash = ? AND status = ? AND use_count < max_uses AND expires_at > ?`,
		GrantStatusRedeemed,
		formatDBTime(at),
		grantHash,
		GrantStatusActive,
		formatDBTime(at),
	)
	if err != nil {
		return Grant{}, fmt.Errorf("redeem grant: %w", err)
	}
	rows, rowsErr := result.RowsAffected()
	if rowsErr == nil && rows > 0 {
		return s.GetGrant(ctx, grantHash)
	}
	grant, getErr := s.GetGrant(ctx, grantHash)
	if getErr != nil {
		return Grant{}, getErr
	}
	switch {
	case grant.Status == GrantStatusRevoked:
		return Grant{}, fmt.Errorf("%w: revoked", ErrGrantNotUsable)
	case grant.Status == GrantStatusExpired || !grant.ExpiresAt.After(at):
		return Grant{}, ErrGrantExpired
	case grant.Status == GrantStatusRedeemed || grant.UseCount >= grant.MaxUses:
		return Grant{}, ErrGrantExhausted
	default:
		return Grant{}, ErrGrantNotUsable
	}
}

func (s *Store) RevokeGrant(ctx context.Context, grantHash, reason string, at time.Time) error {
	if reason == "" {
		reason = "revoked"
	}
	if at.IsZero() {
		at = time.Now().UTC()
	}
	result, err := s.db.ExecContext(ctx, `UPDATE grants SET status = ?, revoked_at = ?, revoke_reason = ? WHERE grant_hash = ? AND status != ?`,
		GrantStatusRevoked, formatDBTime(at), reason, grantHash, GrantStatusRevoked)
	if err != nil {
		return fmt.Errorf("revoke grant: %w", err)
	}
	rows, rowsErr := result.RowsAffected()
	if rowsErr == nil && rows == 0 {
		return ErrGrantNotFound
	}
	return nil
}

func (s *Store) ExpireGrants(ctx context.Context, at time.Time) (int64, error) {
	if at.IsZero() {
		at = time.Now().UTC()
	}
	result, err := s.db.ExecContext(ctx, `UPDATE grants SET status = ? WHERE status = ? AND expires_at <= ?`,
		GrantStatusExpired, GrantStatusActive, formatDBTime(at))
	if err != nil {
		return 0, fmt.Errorf("expire grants: %w", err)
	}
	return result.RowsAffected()
}

func (s *Store) SaveTokenIssue(ctx context.Context, issue TokenIssue) error {
	if issue.ID == "" || issue.GrantHash == "" || issue.AccountID == "" || issue.TokenHash == "" || issue.ExpiresAt.IsZero() {
		return errors.New("token issue id, grant hash, account id, token hash, and expires_at are required")
	}
	if issue.PermissionsJSON == "" {
		issue.PermissionsJSON = "{}"
	}
	if issue.IssuedAt.IsZero() {
		issue.IssuedAt = time.Now().UTC()
	}
	_, err := s.db.ExecContext(ctx, `INSERT INTO token_issues
		(id, grant_hash, account_id, token_hash, expires_at, permissions_json, repository_selection, issued_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
		issue.ID,
		issue.GrantHash,
		issue.AccountID,
		issue.TokenHash,
		formatDBTime(issue.ExpiresAt),
		issue.PermissionsJSON,
		issue.RepositorySelection,
		formatDBTime(issue.IssuedAt),
	)
	if err != nil {
		return fmt.Errorf("save token issue: %w", err)
	}
	return nil
}

func (s *Store) ListTokenIssues(ctx context.Context, accountID string) ([]TokenIssue, error) {
	rows, err := s.db.QueryContext(ctx, `SELECT id, grant_hash, account_id, token_hash, expires_at, permissions_json, repository_selection, issued_at, revoked_at, revoke_reason
		FROM token_issues WHERE account_id = ? ORDER BY issued_at DESC`, accountID)
	if err != nil {
		return nil, fmt.Errorf("list token issues: %w", err)
	}
	defer rows.Close()
	var issues []TokenIssue
	for rows.Next() {
		var issue TokenIssue
		var expiresAt, issuedAt, revokedAt string
		if err := rows.Scan(&issue.ID, &issue.GrantHash, &issue.AccountID, &issue.TokenHash, &expiresAt, &issue.PermissionsJSON, &issue.RepositorySelection, &issuedAt, &revokedAt, &issue.RevokeReason); err != nil {
			return nil, fmt.Errorf("scan token issue: %w", err)
		}
		var err error
		if issue.ExpiresAt, err = parseDBTime(expiresAt); err != nil {
			return nil, err
		}
		if issue.IssuedAt, err = parseDBTime(issuedAt); err != nil {
			return nil, err
		}
		if issue.RevokedAt, err = parseDBTime(revokedAt); err != nil {
			return nil, err
		}
		issues = append(issues, issue)
	}
	return issues, rows.Err()
}

func (s *Store) RevokeTokenIssue(ctx context.Context, issueID, reason string, at time.Time) error {
	if reason == "" {
		reason = "revoked"
	}
	if at.IsZero() {
		at = time.Now().UTC()
	}
	result, err := s.db.ExecContext(ctx, `UPDATE token_issues SET revoked_at = ?, revoke_reason = ? WHERE id = ? AND revoked_at = ''`,
		formatDBTime(at), reason, issueID)
	if err != nil {
		return fmt.Errorf("revoke token issue: %w", err)
	}
	rows, rowsErr := result.RowsAffected()
	if rowsErr == nil && rows == 0 {
		return fmt.Errorf("token issue %q not found or already revoked", issueID)
	}
	return nil
}

func (s *Store) RecordAudit(ctx context.Context, event AuditEvent) error {
	if event.EventType == "" {
		return ErrAuditEventEmpty
	}
	if event.Timestamp.IsZero() {
		event.Timestamp = time.Now().UTC()
	}
	if event.MetadataJSON == "" {
		event.MetadataJSON = "{}"
	}
	_, err := s.db.ExecContext(ctx, `INSERT INTO audit_events
		(timestamp, event_type, actor_type, actor_id, subject_type, subject_id, outcome, code, metadata_json)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		formatDBTime(event.Timestamp),
		event.EventType,
		event.ActorType,
		event.ActorID,
		event.SubjectType,
		event.SubjectID,
		event.Outcome,
		event.Code,
		event.MetadataJSON,
	)
	if err != nil {
		return fmt.Errorf("record audit event: %w", err)
	}
	return nil
}

func parseGrantTimes(grant *Grant, expiresAt, createdAt, redeemedAt, revokedAt string) error {
	var err error
	if grant.ExpiresAt, err = parseDBTime(expiresAt); err != nil {
		return err
	}
	if grant.CreatedAt, err = parseDBTime(createdAt); err != nil {
		return err
	}
	if grant.RedeemedAt, err = parseDBTime(redeemedAt); err != nil {
		return err
	}
	if grant.RevokedAt, err = parseDBTime(revokedAt); err != nil {
		return err
	}
	return nil
}

func parseDBTime(value string) (time.Time, error) {
	if value == "" {
		return time.Time{}, nil
	}
	parsed, err := time.Parse(time.RFC3339Nano, value)
	if err != nil {
		return time.Time{}, fmt.Errorf("parse sqlite timestamp: %w", err)
	}
	return parsed, nil
}
