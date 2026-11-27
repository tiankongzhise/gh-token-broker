package delivery

import (
	"context"
	"errors"
	"path/filepath"
	"testing"
	"time"

	"gh-token-broker/internal/githubapp"
	"gh-token-broker/internal/grant"
	"gh-token-broker/internal/storage/sqlite"
	"gh-token-broker/internal/tokenchain"
)

type fakeParent struct {
	token  tokenchain.ParentToken
	err    error
	minTTL time.Duration
}

func (f *fakeParent) EnsureParentToken(ctx context.Context, accountID string, minTTL time.Duration) (tokenchain.ParentToken, error) {
	f.minTTL = minTTL
	return f.token, f.err
}

type fakeMinter struct {
	result githubapp.ScopedTokenResult
	err    error
	req    githubapp.ScopedTokenRequest
}

func (f *fakeMinter) MintScopedToken(ctx context.Context, req githubapp.ScopedTokenRequest) (githubapp.ScopedTokenResult, error) {
	f.req = req
	return f.result, f.err
}

func openDeliveryTestStore(t *testing.T) *sqlite.Store {
	t.Helper()
	kp, err := sqlite.NewStaticKeyProvider([]byte("0123456789abcdef0123456789abcdef"))
	if err != nil {
		t.Fatal(err)
	}
	store, err := sqlite.Open(context.Background(), filepath.Join(t.TempDir(), "delivery.db"), kp)
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

func setupDelivery(t *testing.T) (*sqlite.Store, string) {
	t.Helper()
	ctx := context.Background()
	store := openDeliveryTestStore(t)
	now := time.Now().UTC()
	if err := store.SaveAuthorizedAccount(ctx, sqlite.Account{
		ID: "account-a", Host: "github.com", ClientID: "client-a", UserLogin: "octo",
		AuthStatus: tokenchain.StatusAuthorized, ParentExpiresAt: now.Add(time.Hour), LastRefreshAt: now,
	}, []byte("test refresh material")); err != nil {
		t.Fatal(err)
	}
	if err := store.PutSecret(ctx, "github/app-client-secret", "github-client-secret", []byte("test client secret")); err != nil {
		t.Fatal(err)
	}
	created, err := grant.NewService(store).Create(ctx, grant.CreateInput{
		AgentID: "agent-a", AccountID: "account-a", Host: "github.com", Owner: "octo",
		Repo: "repo-a", Profile: "repo-read", MinTTL: 2 * time.Hour,
	})
	if err != nil {
		t.Fatal(err)
	}
	return store, created.ID
}

func TestIssueScopedTokenStoresInventoryWithoutRawToken(t *testing.T) {
	ctx := context.Background()
	store, grantID := setupDelivery(t)
	expiresAt := time.Now().Add(3 * time.Hour).UTC()
	parent := &fakeParent{token: tokenchain.ParentToken{Token: "parent-token", ExpiresAt: expiresAt}}
	minter := &fakeMinter{result: githubapp.ScopedTokenResult{
		Token: "scoped-token", ExpiresAt: expiresAt,
		Permissions: map[string]string{"contents": "read"}, RepositorySelection: "selected",
	}}
	service := NewService(store, grant.NewService(store), parent, minter, "github/app-client-secret")
	issued, err := service.IssueScopedToken(ctx, grantID, map[string]string{"contents": "read"})
	if err != nil {
		t.Fatal(err)
	}
	if issued.Token != "scoped-token" || issued.IssueID == "" {
		t.Fatalf("unexpected issued token: %+v", issued)
	}
	if parent.minTTL != 2*time.Hour || minter.req.ParentAccessToken != "parent-token" || minter.req.ClientSecret != "test client secret" {
		t.Fatalf("scoped mint did not use required chain")
	}
	issues, err := store.ListTokenIssues(ctx, "account-a")
	if err != nil {
		t.Fatal(err)
	}
	if len(issues) != 1 || issues[0].TokenHash == issued.Token || issues[0].TokenHash == "scoped-token" {
		t.Fatalf("raw scoped token must not be stored: %+v", issues)
	}
}

func TestIssueScopedTokenFailsClosedOnShortExpiry(t *testing.T) {
	ctx := context.Background()
	store, grantID := setupDelivery(t)
	parent := &fakeParent{token: tokenchain.ParentToken{Token: "parent-token", ExpiresAt: time.Now().Add(3 * time.Hour)}}
	minter := &fakeMinter{result: githubapp.ScopedTokenResult{Token: "scoped-token", ExpiresAt: time.Now().Add(time.Hour)}}
	service := NewService(store, grant.NewService(store), parent, minter, "github/app-client-secret")
	_, err := service.IssueScopedToken(ctx, grantID, map[string]string{"contents": "read"})
	if !errors.Is(err, ErrScopedTokenUnavailable) {
		t.Fatalf("expected scoped unavailable error, got %v", err)
	}
	issues, listErr := store.ListTokenIssues(ctx, "account-a")
	if listErr != nil {
		t.Fatal(listErr)
	}
	if len(issues) != 0 {
		t.Fatalf("short-lived token must not enter inventory")
	}
}

func TestIssueScopedTokenFailsClosedWithoutClientSecret(t *testing.T) {
	ctx := context.Background()
	store, grantID := setupDelivery(t)
	parent := &fakeParent{token: tokenchain.ParentToken{Token: "parent-token", ExpiresAt: time.Now().Add(3 * time.Hour)}}
	minter := &fakeMinter{}
	service := NewService(store, grant.NewService(store), parent, minter, "")
	_, err := service.IssueScopedToken(ctx, grantID, map[string]string{"contents": "read"})
	if !errors.Is(err, ErrScopedTokenUnavailable) {
		t.Fatalf("expected scoped unavailable error, got %v", err)
	}
	if minter.req.ParentAccessToken != "" {
		t.Fatalf("minter must not be called without client secret")
	}
}
