package tokenchain

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"

	"gh-token-broker/internal/githubapp"
	"gh-token-broker/internal/platform/winmutex"
	"gh-token-broker/internal/storage/sqlite"
)

const (
	StatusAuthorized     = "authorized"
	StatusReauthRequired = "reauth_required"
)

var ErrReauthRequired = errors.New("explicit user reauthorization required")

type OAuthClient interface {
	StartDeviceFlow(ctx context.Context, clientID string, scopes []string) (githubapp.DeviceFlowStart, error)
	PollDeviceFlow(ctx context.Context, clientID, deviceCode string) (githubapp.TokenResult, error)
	RefreshToken(ctx context.Context, clientID, refreshToken string) (githubapp.TokenResult, error)
}

type Service struct {
	store *sqlite.Store
	oauth OAuthClient
	skew  time.Duration
	now   func() time.Time

	mu     sync.Mutex
	locks  map[string]*sync.Mutex
	parent map[string]cachedParentToken
}

type cachedParentToken struct {
	token     string
	expiresAt time.Time
}

type ParentToken struct {
	Token     string
	ExpiresAt time.Time
}

func NewService(store *sqlite.Store, oauth OAuthClient, refreshSkew time.Duration) *Service {
	if refreshSkew < 0 {
		refreshSkew = 0
	}
	return &Service{
		store:  store,
		oauth:  oauth,
		skew:   refreshSkew,
		now:    func() time.Time { return time.Now().UTC() },
		locks:  make(map[string]*sync.Mutex),
		parent: make(map[string]cachedParentToken),
	}
}

func (s *Service) BeginDeviceFlow(ctx context.Context, clientID string, scopes []string) (githubapp.DeviceFlowStart, error) {
	if clientID == "" {
		return githubapp.DeviceFlowStart{}, errors.New("client id is required")
	}
	return s.oauth.StartDeviceFlow(ctx, clientID, scopes)
}

func (s *Service) CompleteDeviceFlow(ctx context.Context, accountID, host, clientID, userLogin, deviceCode string) error {
	if accountID == "" || host == "" || clientID == "" || deviceCode == "" {
		return errors.New("account id, host, client id, and device code are required")
	}
	result, err := s.oauth.PollDeviceFlow(ctx, clientID, deviceCode)
	if err != nil {
		return err
	}
	if result.RefreshToken == "" {
		return errors.New("github did not return a refresh token; enable expiring user tokens for the app")
	}
	now := s.now()
	account := sqlite.Account{
		ID:               accountID,
		Host:             host,
		ClientID:         clientID,
		UserLogin:        userLogin,
		AuthStatus:       StatusAuthorized,
		ParentExpiresAt:  now.Add(time.Duration(result.ExpiresIn) * time.Second),
		RefreshExpiresAt: expiryFromSeconds(now, result.RefreshTokenExpiresIn),
		LastRefreshAt:    now,
	}
	refreshSecret := []byte(result.RefreshToken)
	err = s.store.SaveAuthorizedAccount(ctx, account, refreshSecret)
	zeroBytes(refreshSecret)
	if err != nil {
		return err
	}
	s.cacheParent(accountID, result.AccessToken, account.ParentExpiresAt)
	return nil
}

func (s *Service) EnsureParentToken(ctx context.Context, accountID string, minTTL time.Duration) (ParentToken, error) {
	if accountID == "" {
		return ParentToken{}, errors.New("account id is required")
	}
	if cached, ok := s.validCachedParent(accountID, minTTL); ok {
		return cached, nil
	}
	unlockProcess, err := winmutex.Lock("refresh-chain:" + accountID)
	if err != nil {
		return ParentToken{}, fmt.Errorf("acquire refresh chain mutex: %w", err)
	}
	defer unlockProcess()
	lock := s.accountLock(accountID)
	lock.Lock()
	defer lock.Unlock()
	if cached, ok := s.validCachedParent(accountID, minTTL); ok {
		return cached, nil
	}
	account, err := s.store.GetAccount(ctx, accountID)
	if err != nil {
		return ParentToken{}, err
	}
	if account.AuthStatus == StatusReauthRequired {
		code := account.LastErrorCode
		if code == "" {
			code = "reauth_required"
		}
		return ParentToken{}, fmt.Errorf("%w: %s", ErrReauthRequired, code)
	}
	if account.RefreshSecretRef == "" {
		return ParentToken{}, s.markReauthRequired(ctx, accountID, "missing_refresh_token")
	}
	now := s.now()
	if !account.RefreshExpiresAt.IsZero() && !now.Before(account.RefreshExpiresAt) {
		return ParentToken{}, s.markReauthRequired(ctx, accountID, "refresh_token_expired")
	}
	refreshSecret, err := s.store.GetSecret(ctx, account.RefreshSecretRef)
	if err != nil {
		return ParentToken{}, err
	}
	result, err := s.oauth.RefreshToken(ctx, account.ClientID, string(refreshSecret))
	zeroBytes(refreshSecret)
	if err != nil {
		if isRefreshReauthError(err) {
			return ParentToken{}, s.markReauthRequired(ctx, accountID, refreshErrorCode(err))
		}
		return ParentToken{}, err
	}
	if result.RefreshToken == "" {
		return ParentToken{}, s.markReauthRequired(ctx, accountID, "missing_rotated_refresh_token")
	}
	parentExpiresAt := now.Add(time.Duration(result.ExpiresIn) * time.Second)
	refreshExpiresAt := expiryFromSeconds(now, result.RefreshTokenExpiresIn)
	if refreshExpiresAt.IsZero() {
		refreshExpiresAt = account.RefreshExpiresAt
	}
	newRefreshSecret := []byte(result.RefreshToken)
	if err := s.store.RotateRefreshToken(ctx, accountID, newRefreshSecret, parentExpiresAt, refreshExpiresAt, StatusAuthorized, ""); err != nil {
		zeroBytes(newRefreshSecret)
		return ParentToken{}, err
	}
	zeroBytes(newRefreshSecret)
	s.cacheParent(accountID, result.AccessToken, parentExpiresAt)
	return ParentToken{Token: result.AccessToken, ExpiresAt: parentExpiresAt}, nil
}

func (s *Service) markReauthRequired(ctx context.Context, accountID, code string) error {
	if updateErr := s.store.UpdateAccountState(ctx, accountID, StatusReauthRequired, code); updateErr != nil {
		return fmt.Errorf("mark reauth required: %w", updateErr)
	}
	return fmt.Errorf("%w: %s", ErrReauthRequired, code)
}

func (s *Service) accountLock(accountID string) *sync.Mutex {
	s.mu.Lock()
	defer s.mu.Unlock()
	lock, ok := s.locks[accountID]
	if !ok {
		lock = &sync.Mutex{}
		s.locks[accountID] = lock
	}
	return lock
}

func (s *Service) validCachedParent(accountID string, minTTL time.Duration) (ParentToken, bool) {
	requiredUntil := s.now().Add(minTTL).Add(s.skew)
	s.mu.Lock()
	cached, ok := s.parent[accountID]
	s.mu.Unlock()
	if !ok || cached.token == "" || cached.expiresAt.IsZero() || !cached.expiresAt.After(requiredUntil) {
		return ParentToken{}, false
	}
	return ParentToken{Token: cached.token, ExpiresAt: cached.expiresAt}, true
}

func (s *Service) cacheParent(accountID, token string, expiresAt time.Time) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.parent[accountID] = cachedParentToken{token: token, expiresAt: expiresAt}
}

func expiryFromSeconds(now time.Time, seconds int) time.Time {
	if seconds <= 0 {
		return time.Time{}
	}
	return now.Add(time.Duration(seconds) * time.Second)
}

func isRefreshReauthError(err error) bool {
	var apiErr *githubapp.APIError
	if !errors.As(err, &apiErr) {
		return false
	}
	switch apiErr.Code {
	case "bad_refresh_token", "invalid_grant", "token_expired", "unauthorized":
		return true
	default:
		return false
	}
}

func refreshErrorCode(err error) string {
	var apiErr *githubapp.APIError
	if errors.As(err, &apiErr) && apiErr.Code != "" {
		return apiErr.Code
	}
	return "refresh_failed"
}

func zeroBytes(value []byte) {
	for i := range value {
		value[i] = 0
	}
}
