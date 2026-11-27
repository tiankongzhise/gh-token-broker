package grant

import (
	"context"
	"errors"
	"path/filepath"
	"testing"
	"time"

	"gh-token-broker/internal/storage/sqlite"
)

func openGrantTestStore(t *testing.T) *sqlite.Store {
	t.Helper()
	kp, err := sqlite.NewStaticKeyProvider([]byte("0123456789abcdef0123456789abcdef"))
	if err != nil {
		t.Fatal(err)
	}
	store, err := sqlite.Open(context.Background(), filepath.Join(t.TempDir(), "grant.db"), kp)
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

func TestGrantLifecycleStoresHashAndRedeemsOnce(t *testing.T) {
	ctx := context.Background()
	store := openGrantTestStore(t)
	service := NewService(store)
	created, err := service.Create(ctx, CreateInput{
		AgentID:   "agent-a",
		AccountID: "account-a",
		Host:      "github.com",
		Owner:     "octo",
		Repo:      "repo-a",
		Profile:   "repo-read",
		MinTTL:    2 * time.Hour,
	})
	if err != nil {
		t.Fatal(err)
	}
	if created.ID == "" || created.Grant.GrantHash == "" || created.Grant.GrantHash == created.ID {
		t.Fatalf("grant id was not separated from stored hash")
	}
	redeemed, err := service.Redeem(ctx, created.ID)
	if err != nil {
		t.Fatal(err)
	}
	if redeemed.Status != sqlite.GrantStatusRedeemed || redeemed.UseCount != 1 || redeemed.RedeemedAt.IsZero() {
		t.Fatalf("unexpected redeemed grant: %+v", redeemed)
	}
	if _, err := service.Redeem(ctx, created.ID); !errors.Is(err, sqlite.ErrGrantExhausted) {
		t.Fatalf("expected exhausted grant error, got %v", err)
	}
}

func TestGrantRevokeAndExpiration(t *testing.T) {
	ctx := context.Background()
	store := openGrantTestStore(t)
	service := NewService(store)
	input := CreateInput{
		AgentID:   "agent-a",
		AccountID: "account-a",
		Host:      "github.com",
		Owner:     "octo",
		Repo:      "repo-a",
		Profile:   "repo-read",
		MinTTL:    time.Hour,
		TTL:       time.Millisecond,
	}
	revoked, err := service.Create(ctx, input)
	if err != nil {
		t.Fatal(err)
	}
	if err := service.Revoke(ctx, revoked.ID, "operator revoked"); err != nil {
		t.Fatal(err)
	}
	if _, err := service.Redeem(ctx, revoked.ID); !errors.Is(err, sqlite.ErrGrantNotUsable) {
		t.Fatalf("expected revoked grant error, got %v", err)
	}

	expired, err := service.Create(ctx, input)
	if err != nil {
		t.Fatal(err)
	}
	time.Sleep(2 * time.Millisecond)
	if _, err := service.Redeem(ctx, expired.ID); !errors.Is(err, sqlite.ErrGrantExpired) {
		t.Fatalf("expected expired grant error, got %v", err)
	}
}
