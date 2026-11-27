package githubapp

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestDeviceFlowAndRefreshAgainstMockGitHub(t *testing.T) {
	var sawDeviceStart, sawPoll, sawRefresh bool
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("unexpected method %s", r.Method)
		}
		if err := r.ParseForm(); err != nil {
			t.Errorf("parse form: %v", err)
		}
		w.Header().Set("Content-Type", "application/json")
		switch r.URL.Path {
		case "/login/device/code":
			sawDeviceStart = true
			if r.Form.Get("client_id") != "test-client" || r.Form.Get("scope") != "offline_access" {
				t.Errorf("unexpected device start form: %v", r.Form)
			}
			json.NewEncoder(w).Encode(map[string]any{
				"device_code":      "test-device-code",
				"user_code":        "TEST-CODE",
				"verification_uri": serverURLPlaceholder(r),
				"expires_in":       900,
				"interval":         5,
			})
		case "/login/oauth/access_token":
			switch r.Form.Get("grant_type") {
			case "urn:ietf:params:oauth:grant-type:device_code":
				sawPoll = true
				if r.Form.Get("device_code") != "test-device-code" {
					t.Errorf("unexpected device code")
				}
				json.NewEncoder(w).Encode(map[string]any{
					"access_token":             "test-access-token",
					"token_type":               "bearer",
					"refresh_token":            "test-refresh-token",
					"expires_in":               28800,
					"refresh_token_expires_in": 16000000,
				})
			case "refresh_token":
				sawRefresh = true
				if r.Form.Get("refresh_token") != "test-refresh-token" {
					t.Errorf("unexpected refresh token form value")
				}
				json.NewEncoder(w).Encode(map[string]any{
					"access_token":             "test-new-access-token",
					"token_type":               "bearer",
					"refresh_token":            "test-new-refresh-token",
					"expires_in":               28800,
					"refresh_token_expires_in": 16000000,
				})
			default:
				t.Errorf("unexpected grant type %q", r.Form.Get("grant_type"))
			}
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	client := New(server.URL)
	ctx := context.Background()
	start, err := client.StartDeviceFlow(ctx, "test-client", []string{"offline_access"})
	if err != nil {
		t.Fatal(err)
	}
	if start.DeviceCode == "" || start.UserCode == "" {
		t.Fatalf("device flow start missing fields: %+v", start)
	}
	poll, err := client.PollDeviceFlow(ctx, "test-client", start.DeviceCode)
	if err != nil {
		t.Fatal(err)
	}
	if poll.AccessToken == "" || poll.RefreshToken == "" {
		t.Fatalf("poll missing token fields")
	}
	refresh, err := client.RefreshToken(ctx, "test-client", "test-refresh-token")
	if err != nil {
		t.Fatal(err)
	}
	if refresh.AccessToken != "test-new-access-token" || refresh.RefreshToken != "test-new-refresh-token" {
		t.Fatalf("unexpected refresh result")
	}
	if !sawDeviceStart || !sawPoll || !sawRefresh {
		t.Fatalf("mock endpoints not all called: start=%v poll=%v refresh=%v", sawDeviceStart, sawPoll, sawRefresh)
	}
}

func serverURLPlaceholder(r *http.Request) string {
	return "http://" + r.Host + "/login/device"
}

func TestOAuthErrorResponse(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{
			"error":             "bad_refresh_token",
			"error_description": "test refresh token rejected",
		})
	}))
	defer server.Close()
	client := New(server.URL)
	_, err := client.RefreshToken(context.Background(), "test-client", "test-refresh-token")
	var apiErr *APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("expected APIError, got %T: %v", err, err)
	}
	if apiErr.Code != "bad_refresh_token" {
		t.Fatalf("unexpected API error code %q", apiErr.Code)
	}
}
