package githubapp

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

type ScopedClient struct {
	APIBaseURL string
	HTTPClient *http.Client
	UserAgent  string
}

type ScopedTokenRequest struct {
	ClientID          string
	ClientSecret      string
	ParentAccessToken string
	Target            string
	Repositories      []string
	Permissions       map[string]string
}

type ScopedTokenResult struct {
	Token               string
	ExpiresAt           time.Time
	Permissions         map[string]string
	RepositorySelection string
}

type scopedTokenResponse struct {
	Token               string            `json:"token"`
	AccessToken         string            `json:"access_token"`
	ExpiresAt           string            `json:"expires_at"`
	Permissions         map[string]string `json:"permissions"`
	RepositorySelection string            `json:"repository_selection"`
}

func NewScopedClient(apiBaseURL string) *ScopedClient {
	return &ScopedClient{
		APIBaseURL: strings.TrimRight(apiBaseURL, "/"),
		HTTPClient: &http.Client{Timeout: 15 * time.Second},
		UserAgent:  "gh-token-broker-phase2",
	}
}

func (c *ScopedClient) MintScopedToken(ctx context.Context, reqInput ScopedTokenRequest) (ScopedTokenResult, error) {
	if reqInput.ClientID == "" || reqInput.ClientSecret == "" || reqInput.ParentAccessToken == "" {
		return ScopedTokenResult{}, errors.New("client id, client secret, and parent access token are required")
	}
	if reqInput.Target == "" || len(reqInput.Repositories) == 0 || len(reqInput.Permissions) == 0 {
		return ScopedTokenResult{}, errors.New("target, repositories, and permissions are required")
	}
	payload := map[string]any{
		"access_token": reqInput.ParentAccessToken,
		"target":       reqInput.Target,
		"repositories": reqInput.Repositories,
		"permissions":  reqInput.Permissions,
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return ScopedTokenResult{}, err
	}
	httpClient := c.HTTPClient
	if httpClient == nil {
		httpClient = http.DefaultClient
	}
	url := c.APIBaseURL + "/applications/" + reqInput.ClientID + "/token/scoped"
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return ScopedTokenResult{}, err
	}
	req.SetBasicAuth(reqInput.ClientID, reqInput.ClientSecret)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-GitHub-Api-Version", "2022-11-28")
	if c.UserAgent != "" {
		req.Header.Set("User-Agent", c.UserAgent)
	}
	resp, err := httpClient.Do(req)
	if err != nil {
		return ScopedTokenResult{}, fmt.Errorf("github scoped token request failed: %w", err)
	}
	defer resp.Body.Close()
	respBody, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return ScopedTokenResult{}, fmt.Errorf("read scoped token response: %w", err)
	}
	if resp.StatusCode < 200 || resp.StatusCode > 299 {
		return ScopedTokenResult{}, &APIError{StatusCode: resp.StatusCode, Code: "scoped_token_http_error", Description: http.StatusText(resp.StatusCode)}
	}
	var decoded scopedTokenResponse
	if err := json.Unmarshal(respBody, &decoded); err != nil {
		return ScopedTokenResult{}, fmt.Errorf("decode scoped token response: %w", err)
	}
	token := decoded.Token
	if token == "" {
		token = decoded.AccessToken
	}
	if token == "" {
		return ScopedTokenResult{}, errors.New("scoped token response missing token")
	}
	if decoded.ExpiresAt == "" {
		return ScopedTokenResult{}, errors.New("scoped token response missing expires_at")
	}
	expiresAt, err := time.Parse(time.RFC3339, decoded.ExpiresAt)
	if err != nil {
		return ScopedTokenResult{}, fmt.Errorf("scoped token response has invalid expires_at: %w", err)
	}
	return ScopedTokenResult{Token: token, ExpiresAt: expiresAt, Permissions: decoded.Permissions, RepositorySelection: decoded.RepositorySelection}, nil
}
