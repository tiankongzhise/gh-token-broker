package sqlite

import (
	"context"
	"database/sql"
	"errors"
	"testing"
	"time"
)

func TestGrantPersistenceAndRedeemRules(t *testing.T) {
	ctx := context.Background()
	store := openTestStore(t)
	now := time.Now().UTC()
	grant := Grant{
		GrantHash: "hash-a",
		AgentID:   "agent-a",
		AccountID: "account-a",
		Host:      "github.com",
		Owner:     "octo",
		Repo:      "repo-a",
		Profile:   "repo-read",
		MinTTL:    2 * time.Hour,
		ExpiresAt: now.Add(10 * time.Minute),
		MaxUses:   2,
		Status:    GrantStatusActive,
		CreatedAt: now,
	}
	if err := store.CreateGrant(ctx, grant); err != nil {
		t.Fatal(err)
	}
	var plaintextID string
	if err := store.db.QueryRowContext(ctx, `SELECT grant_hash FROM grants WHERE grant_hash = ?`, "grt_plaintext").Scan(&plaintextID); !errors.Is(err, sql.ErrNoRows) {
		t.Fatalf("unexpected plaintext grant id lookup result: %v", err)
	}
	got, err := store.GetGrant(ctx, grant.GrantHash)
	if err != nil {
		t.Fatal(err)
	}
	if got.MinTTL != grant.MinTTL || got.Status != GrantStatusActive {
		t.Fatalf("unexpected grant: %+v", got)
	}
	first, err := store.RedeemGrant(ctx, grant.GrantHash, now.Add(time.Second))
	if err != nil {
		t.Fatal(err)
	}
	if first.Status != GrantStatusActive || first.UseCount != 1 {
		t.Fatalf("first redemption should keep multi-use grant active: %+v", first)
	}
	second, err := store.RedeemGrant(ctx, grant.GrantHash, now.Add(2*time.Second))
	if err != nil {
		t.Fatal(err)
	}
	if second.Status != GrantStatusRedeemed || second.UseCount != 2 {
		t.Fatalf("second redemption should exhaust grant: %+v", second)
	}
	if _, err := store.RedeemGrant(ctx, grant.GrantHash, now.Add(3*time.Second)); !errors.Is(err, ErrGrantExhausted) {
		t.Fatalf("expected exhausted error, got %v", err)
	}
}

func TestTokenIssueInventoryAndAudit(t *testing.T) {
	ctx := context.Background()
	store := openTestStore(t)
	now := time.Now().UTC()
	issue := TokenIssue{
		ID:                  "issue-a",
		GrantHash:           "hash-a",
		AccountID:           "account-a",
		TokenHash:           "token-hash-a",
		ExpiresAt:           now.Add(time.Hour),
		PermissionsJSON:     `{"contents":"read"}`,
		RepositorySelection: "selected",
		IssuedAt:            now,
	}
	if err := store.SaveTokenIssue(ctx, issue); err != nil {
		t.Fatal(err)
	}
	issues, err := store.ListTokenIssues(ctx, "account-a")
	if err != nil {
		t.Fatal(err)
	}
	if len(issues) != 1 || issues[0].TokenHash == "raw-token" {
		t.Fatalf("unexpected inventory: %+v", issues)
	}
	if err := store.RevokeTokenIssue(ctx, issue.ID, "test revoke", now.Add(time.Minute)); err != nil {
		t.Fatal(err)
	}
	if err := store.RecordAudit(ctx, AuditEvent{EventType: "grant_redeemed", SubjectType: "grant", SubjectID: issue.GrantHash, Outcome: "success"}); err != nil {
		t.Fatal(err)
	}
	var auditCount int
	if err := store.db.QueryRowContext(ctx, `SELECT COUNT(*) FROM audit_events`).Scan(&auditCount); err != nil {
		t.Fatal(err)
	}
	if auditCount != 1 {
		t.Fatalf("expected one audit event, got %d", auditCount)
	}
}
