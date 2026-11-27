package tokenchain

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"gh-token-broker/internal/githubapp"
	"gh-token-broker/internal/storage/sqlite"
)

func openTokenTestStore(t *testing.T) *sqlite.Store {
	t.Helper()
	key := make([]byte, 32)
	for i := range key {
		key[i] = byte(i + 1)
	}
	kp, err := sqlite.NewStaticKeyProvider(key)
	if err != nil {
		t.Fatal(err)
	}
	store, err := sqlite.Open(context.Background(), filepath.Join(t.TempDir(), "tokenchain.db"), kp)
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

func saveTestAccount(t *testing.T, ctx context.Context, store *sqlite.Store) {
	t.Helper()
	account := sqlite.Account{
		ID:               "acct-test",
		Host:             "github.com",
		ClientID:         "test-client",
		UserLogin:        "test-user",
		AuthStatus:       StatusAuthorized,
		RefreshExpiresAt: time.Now().UTC().Add(24 * time.Hour),
	}
	if err := store.SaveAuthorizedAccount(ctx, account, []byte("test-initial-refresh-token")); err != nil {
		t.Fatal(err)
	}
}

func TestConcurrentEnsureParentTokenRefreshesOnce(t *testing.T) {
	ctx := context.Background()
	store := openTokenTestStore(t)
	saveTestAccount(t, ctx, store)

	var refreshCalls atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/login/oauth/access_token" {
			http.NotFound(w, r)
			return
		}
		if err := r.ParseForm(); err != nil {
			t.Errorf("parse form: %v", err)
		}
		if r.Form.Get("grant_type") != "refresh_token" || r.Form.Get("refresh_token") != "test-initial-refresh-token" {
			t.Errorf("unexpected refresh form: %v", r.Form)
		}
		refreshCalls.Add(1)
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"access_token":             "test-parent-token",
			"token_type":               "bearer",
			"refresh_token":            "test-rotated-refresh-token",
			"expires_in":               28800,
			"refresh_token_expires_in": 16000000,
		})
	}))
	defer server.Close()

	service := NewService(store, githubapp.New(server.URL), 0)
	const workers = 8
	var wg sync.WaitGroup
	errs := make(chan error, workers)
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			token, err := service.EnsureParentToken(ctx, "acct-test", time.Minute)
			if err != nil {
				errs <- err
				return
			}
			if token.Token != "test-parent-token" {
				errs <- errors.New("unexpected parent token")
			}
		}()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
	if got := refreshCalls.Load(); got != 1 {
		t.Fatalf("expected exactly one refresh call, got %d", got)
	}
	storedRefresh, err := store.GetSecret(ctx, sqlite.RefreshSecretRef("acct-test"))
	if err != nil {
		t.Fatal(err)
	}
	if string(storedRefresh) != "test-rotated-refresh-token" {
		t.Fatalf("refresh token was not rotated transactionally")
	}
}

func TestBadRefreshTokenMarksReauthRequired(t *testing.T) {
	ctx := context.Background()
	store := openTokenTestStore(t)
	saveTestAccount(t, ctx, store)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{
			"error":             "bad_refresh_token",
			"error_description": "test refresh rejected",
		})
	}))
	defer server.Close()

	service := NewService(store, githubapp.New(server.URL), 0)
	_, err := service.EnsureParentToken(ctx, "acct-test", time.Minute)
	if !errors.Is(err, ErrReauthRequired) {
		t.Fatalf("expected ErrReauthRequired, got %v", err)
	}
	account, err := store.GetAccount(ctx, "acct-test")
	if err != nil {
		t.Fatal(err)
	}
	if account.AuthStatus != StatusReauthRequired || account.LastErrorCode != "bad_refresh_token" {
		t.Fatalf("unexpected account state: %+v", account)
	}
}

func TestMissingRotatedRefreshTokenMarksReauthAndDoesNotRetry(t *testing.T) {
	ctx := context.Background()
	store := openTokenTestStore(t)
	saveTestAccount(t, ctx, store)
	var refreshCalls atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		refreshCalls.Add(1)
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"access_token": "test-parent-token",
			"token_type":   "bearer",
			"expires_in":   28800,
		})
	}))
	defer server.Close()

	service := NewService(store, githubapp.New(server.URL), 0)
	if _, err := service.EnsureParentToken(ctx, "acct-test", time.Minute); !errors.Is(err, ErrReauthRequired) {
		t.Fatalf("expected ErrReauthRequired, got %v", err)
	}
	if _, err := service.EnsureParentToken(ctx, "acct-test", time.Minute); !errors.Is(err, ErrReauthRequired) {
		t.Fatalf("expected cached reauth state, got %v", err)
	}
	if got := refreshCalls.Load(); got != 1 {
		t.Fatalf("expected one refresh attempt, got %d", got)
	}
	account, err := store.GetAccount(ctx, "acct-test")
	if err != nil {
		t.Fatal(err)
	}
	if account.LastErrorCode != "missing_rotated_refresh_token" {
		t.Fatalf("unexpected last error code %q", account.LastErrorCode)
	}
}

func TestCompleteDeviceFlowPersistsRefreshChain(t *testing.T) {
	ctx := context.Background()
	store := openTokenTestStore(t)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if r.URL.Path != "/login/oauth/access_token" {
			http.NotFound(w, r)
			return
		}
		if err := r.ParseForm(); err != nil {
			t.Errorf("parse form: %v", err)
		}
		if r.Form.Get("grant_type") != "urn:ietf:params:oauth:grant-type:device_code" {
			t.Errorf("unexpected grant type")
		}
		json.NewEncoder(w).Encode(map[string]any{
			"access_token":             "test-device-parent-token",
			"token_type":               "bearer",
			"refresh_token":            "test-device-refresh-token",
			"expires_in":               28800,
			"refresh_token_expires_in": 16000000,
		})
	}))
	defer server.Close()

	service := NewService(store, githubapp.New(server.URL), 0)
	if err := service.CompleteDeviceFlow(ctx, "acct-device", "github.com", "test-client", "test-user", "test-device-code"); err != nil {
		t.Fatal(err)
	}
	account, err := store.GetAccount(ctx, "acct-device")
	if err != nil {
		t.Fatal(err)
	}
	if account.AuthStatus != StatusAuthorized || account.RefreshSecretRef == "" {
		t.Fatalf("unexpected account after device flow: %+v", account)
	}
	storedRefresh, err := store.GetSecret(ctx, account.RefreshSecretRef)
	if err != nil {
		t.Fatal(err)
	}
	if string(storedRefresh) != "test-device-refresh-token" {
		t.Fatalf("device flow refresh token was not persisted")
	}
}
