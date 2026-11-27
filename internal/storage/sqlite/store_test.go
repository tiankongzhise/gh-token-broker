package sqlite

import (
	"bytes"
	"context"
	"path/filepath"
	"testing"
	"time"
)

func testKeyProvider(t *testing.T) StaticKeyProvider {
	t.Helper()
	kp, err := NewStaticKeyProvider(bytes.Repeat([]byte{0x42}, masterKeySize))
	if err != nil {
		t.Fatal(err)
	}
	return kp
}

func openTestStore(t *testing.T) *Store {
	t.Helper()
	store, err := Open(context.Background(), filepath.Join(t.TempDir(), "test.db"), testKeyProvider(t))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := store.Close(); err != nil {
			t.Errorf("close store: %v", err)
		}
	})
	return store
}

func TestSecretRoundTripAndRandomNonce(t *testing.T) {
	ctx := context.Background()
	store := openTestStore(t)
	ref := "test/refresh-token"
	plaintext := []byte("test refresh plaintext")

	if err := store.PutSecret(ctx, ref, RefreshTokenKind, plaintext); err != nil {
		t.Fatal(err)
	}
	got, err := store.GetSecret(ctx, ref)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, plaintext) {
		t.Fatalf("plaintext mismatch")
	}

	var firstNonce, secondNonce []byte
	if err := store.db.QueryRowContext(ctx, `SELECT nonce FROM secrets WHERE ref = ?`, ref).Scan(&firstNonce); err != nil {
		t.Fatal(err)
	}
	if err := store.PutSecret(ctx, ref, RefreshTokenKind, plaintext); err != nil {
		t.Fatal(err)
	}
	if err := store.db.QueryRowContext(ctx, `SELECT nonce FROM secrets WHERE ref = ?`, ref).Scan(&secondNonce); err != nil {
		t.Fatal(err)
	}
	if bytes.Equal(firstNonce, secondNonce) {
		t.Fatalf("nonce was reused")
	}
}

func TestSecretAuthenticationFailsAfterTamper(t *testing.T) {
	ctx := context.Background()
	store := openTestStore(t)
	ref := "test/tampered-secret"
	if err := store.PutSecret(ctx, ref, RefreshTokenKind, []byte("test secret material")); err != nil {
		t.Fatal(err)
	}
	if _, err := store.db.ExecContext(ctx, `UPDATE secrets SET ciphertext = substr(ciphertext, 1, length(ciphertext)-1) || char(0) WHERE ref = ?`, ref); err != nil {
		t.Fatal(err)
	}
	if _, err := store.GetSecret(ctx, ref); err == nil {
		t.Fatalf("expected authentication failure for tampered ciphertext")
	}
}

func TestRotateRefreshTokenRollsBackSecretWhenAccountMissing(t *testing.T) {
	ctx := context.Background()
	store := openTestStore(t)
	accountID := "missing-account"
	now := time.Now().UTC()
	err := store.RotateRefreshToken(ctx, accountID, []byte("test rotated refresh plaintext"), now, now, "authorized", "")
	if err == nil {
		t.Fatalf("expected missing account error")
	}
	if _, err := store.GetSecret(ctx, RefreshSecretRef(accountID)); err == nil {
		t.Fatalf("secret insert was not rolled back")
	}
}

func TestWrongKeyCannotDecrypt(t *testing.T) {
	ctx := context.Background()
	path := filepath.Join(t.TempDir(), "wrong-key.db")
	first, err := Open(ctx, path, testKeyProvider(t))
	if err != nil {
		t.Fatal(err)
	}
	if err := first.PutSecret(ctx, "test/secret", RefreshTokenKind, []byte("test secret material")); err != nil {
		t.Fatal(err)
	}
	if err := first.Close(); err != nil {
		t.Fatal(err)
	}

	wrongKey, err := NewStaticKeyProvider(bytes.Repeat([]byte{0x24}, masterKeySize))
	if err != nil {
		t.Fatal(err)
	}
	second, err := Open(ctx, path, wrongKey)
	if err != nil {
		t.Fatal(err)
	}
	defer second.Close()
	if _, err := second.GetSecret(ctx, "test/secret"); err == nil {
		t.Fatalf("expected decryption failure with wrong key")
	}
}
