package githubapp

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

type Client struct {
	BaseURL    string
	HTTPClient *http.Client
	UserAgent  string
}

type DeviceFlowStart struct {
	DeviceCode              string `json:"device_code"`
	UserCode                string `json:"user_code"`
	VerificationURI         string `json:"verification_uri"`
	VerificationURIComplete string `json:"verification_uri_complete"`
	ExpiresIn               int    `json:"expires_in"`
	Interval                int    `json:"interval"`
}

type TokenResult struct {
	AccessToken           string `json:"access_token"`
	TokenType             string `json:"token_type"`
	Scope                 string `json:"scope"`
	RefreshToken          string `json:"refresh_token"`
	ExpiresIn             int    `json:"expires_in"`
	RefreshTokenExpiresIn int    `json:"refresh_token_expires_in"`
}

type APIError struct {
	StatusCode  int
	Code        string
	Description string
}

func (e *APIError) Error() string {
	if e.Description == "" {
		return fmt.Sprintf("github oauth error %s (http %d)", e.Code, e.StatusCode)
	}
	return fmt.Sprintf("github oauth error %s (http %d): %s", e.Code, e.StatusCode, e.Description)
}

func New(baseURL string) *Client {
	return &Client{
		BaseURL: strings.TrimRight(baseURL, "/"),
		HTTPClient: &http.Client{
			Timeout: 15 * time.Second,
		},
		UserAgent: "gh-token-broker-phase1-poc",
	}
}

func (c *Client) StartDeviceFlow(ctx context.Context, clientID string, scopes []string) (DeviceFlowStart, error) {
	form := url.Values{
		"client_id": {clientID},
	}
	if len(scopes) > 0 {
		form.Set("scope", strings.Join(scopes, " "))
	}
	var out DeviceFlowStart
	if err := c.postForm(ctx, "/login/device/code", form, &out); err != nil {
		return DeviceFlowStart{}, err
	}
	if out.DeviceCode == "" || out.UserCode == "" || out.VerificationURI == "" {
		return DeviceFlowStart{}, fmt.Errorf("github device flow response missing required fields")
	}
	return out, nil
}

func (c *Client) PollDeviceFlow(ctx context.Context, clientID, deviceCode string) (TokenResult, error) {
	form := url.Values{
		"client_id":   {clientID},
		"device_code": {deviceCode},
		"grant_type":  {"urn:ietf:params:oauth:grant-type:device_code"},
	}
	var out TokenResult
	if err := c.postForm(ctx, "/login/oauth/access_token", form, &out); err != nil {
		return TokenResult{}, err
	}
	return validateTokenResult(out)
}

func (c *Client) RefreshToken(ctx context.Context, clientID, refreshToken string) (TokenResult, error) {
	form := url.Values{
		"client_id":     {clientID},
		"refresh_token": {refreshToken},
		"grant_type":    {"refresh_token"},
	}
	var out TokenResult
	if err := c.postForm(ctx, "/login/oauth/access_token", form, &out); err != nil {
		return TokenResult{}, err
	}
	return validateTokenResult(out)
}

func validateTokenResult(out TokenResult) (TokenResult, error) {
	if out.AccessToken == "" {
		return TokenResult{}, fmt.Errorf("github token response missing access token")
	}
	if out.ExpiresIn <= 0 {
		return TokenResult{}, fmt.Errorf("github token response missing positive expires_in")
	}
	return out, nil
}

func (c *Client) postForm(ctx context.Context, path string, form url.Values, out any) error {
	httpClient := c.HTTPClient
	if httpClient == nil {
		httpClient = http.DefaultClient
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.BaseURL+path, strings.NewReader(form.Encode()))
	if err != nil {
		return err
	}
	req.Header.Set("Accept", "application/json")
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	if c.UserAgent != "" {
		req.Header.Set("User-Agent", c.UserAgent)
	}
	resp, err := httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("github oauth request failed: %w", err)
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return fmt.Errorf("read github oauth response: %w", err)
	}
	var oauthErr struct {
		Error            string `json:"error"`
		ErrorDescription string `json:"error_description"`
	}
	if err := json.Unmarshal(body, &oauthErr); err == nil && oauthErr.Error != "" {
		return &APIError{StatusCode: resp.StatusCode, Code: oauthErr.Error, Description: oauthErr.ErrorDescription}
	}
	if resp.StatusCode < 200 || resp.StatusCode > 299 {
		return &APIError{StatusCode: resp.StatusCode, Code: "http_error", Description: http.StatusText(resp.StatusCode)}
	}
	if err := json.Unmarshal(body, out); err != nil {
		return fmt.Errorf("decode github oauth response: %w", err)
	}
	return nil
}
