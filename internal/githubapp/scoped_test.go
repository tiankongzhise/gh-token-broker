package githubapp

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestMintScopedTokenAgainstMockGitHub(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/applications/test-client/token/scoped" {
			t.Errorf("unexpected path %s", r.URL.Path)
		}
		wantAuth := "Basic " + base64.StdEncoding.EncodeToString([]byte("test-client:test-secret"))
		if r.Header.Get("Authorization") != wantAuth {
			t.Errorf("unexpected authorization header")
		}
		var payload map[string]any
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			t.Errorf("decode request: %v", err)
		}
		if payload["access_token"] != "parent-token" || payload["target"] != "acme" {
			t.Errorf("unexpected payload: %#v", payload)
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"token":                "scoped-token",
			"expires_at":           time.Now().Add(2 * time.Hour).UTC().Format(time.RFC3339),
			"permissions":          map[string]string{"contents": "read"},
			"repository_selection": "selected",
		})
	}))
	defer server.Close()
	client := NewScopedClient(server.URL)
	result, err := client.MintScopedToken(context.Background(), ScopedTokenRequest{
		ClientID: "test-client", ClientSecret: "test-secret", ParentAccessToken: "parent-token",
		Target: "acme", Repositories: []string{"repo-a"}, Permissions: map[string]string{"contents": "read"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if result.Token != "scoped-token" || result.ExpiresAt.IsZero() || result.Permissions["contents"] != "read" {
		t.Fatalf("unexpected scoped result: %+v", result)
	}
}

func TestMintScopedTokenRejectsMissingExpiry(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{"token": "scoped-token"})
	}))
	defer server.Close()
	client := NewScopedClient(server.URL)
	_, err := client.MintScopedToken(context.Background(), ScopedTokenRequest{
		ClientID: "test-client", ClientSecret: "test-secret", ParentAccessToken: "parent-token",
		Target: "acme", Repositories: []string{"repo-a"}, Permissions: map[string]string{"contents": "read"},
	})
	if err == nil {
		t.Fatal("expected missing expires_at error")
	}
}
