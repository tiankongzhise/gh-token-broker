package delivery

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"gh-token-broker/internal/githubapp"
	"gh-token-broker/internal/storage/sqlite"
	"gh-token-broker/internal/tokenchain"
)

var ErrScopedTokenUnavailable = errors.New("scoped token unavailable")

type GrantRedeemer interface {
	Redeem(ctx context.Context, id string) (sqlite.Grant, error)
}

type ParentTokenService interface {
	EnsureParentToken(ctx context.Context, accountID string, minTTL time.Duration) (tokenchain.ParentToken, error)
}

type ScopedMinter interface {
	MintScopedToken(ctx context.Context, req githubapp.ScopedTokenRequest) (githubapp.ScopedTokenResult, error)
}

type Store interface {
	GetAccount(ctx context.Context, id string) (sqlite.Account, error)
	GetSecret(ctx context.Context, ref string) ([]byte, error)
	SaveTokenIssue(ctx context.Context, issue sqlite.TokenIssue) error
	RecordAudit(ctx context.Context, event sqlite.AuditEvent) error
}

type Service struct {
	store           Store
	grants          GrantRedeemer
	parent          ParentTokenService
	minter          ScopedMinter
	clientSecretRef string
	now             func() time.Time
}

type ScopedToken struct {
	GrantHash string
	Token     string
	ExpiresAt time.Time
	IssueID   string
}

func NewService(store Store, grants GrantRedeemer, parent ParentTokenService, minter ScopedMinter, clientSecretRef string) *Service {
	return &Service{
		store:           store,
		grants:          grants,
		parent:          parent,
		minter:          minter,
		clientSecretRef: clientSecretRef,
		now:             func() time.Time { return time.Now().UTC() },
	}
}

func (s *Service) IssueScopedToken(ctx context.Context, grantID string, permissions map[string]string) (ScopedToken, error) {
	if len(permissions) == 0 {
		return ScopedToken{}, fmt.Errorf("%w: permissions are required", ErrScopedTokenUnavailable)
	}
	if s.clientSecretRef == "" {
		return ScopedToken{}, fmt.Errorf("%w: client secret ref is not configured", ErrScopedTokenUnavailable)
	}
	grant, err := s.grants.Redeem(ctx, grantID)
	if err != nil {
		return ScopedToken{}, fmt.Errorf("redeem grant: %w", err)
	}
	if err := s.recordAudit(ctx, "grant_redeemed", grant.AgentID, "grant", grant.GrantHash, "success", ""); err != nil {
		return ScopedToken{}, err
	}
	parent, err := s.parent.EnsureParentToken(ctx, grant.AccountID, grant.MinTTL)
	if err != nil {
		return ScopedToken{}, fmt.Errorf("%w: %v", ErrScopedTokenUnavailable, err)
	}
	account, err := s.store.GetAccount(ctx, grant.AccountID)
	if err != nil {
		return ScopedToken{}, err
	}
	clientSecret, err := s.store.GetSecret(ctx, s.clientSecretRef)
	if err != nil {
		return ScopedToken{}, fmt.Errorf("%w: client secret unavailable", ErrScopedTokenUnavailable)
	}
	result, err := s.minter.MintScopedToken(ctx, githubapp.ScopedTokenRequest{
		ClientID:          account.ClientID,
		ClientSecret:      string(clientSecret),
		ParentAccessToken: parent.Token,
		Target:            grant.Owner,
		Repositories:      []string{grant.Repo},
		Permissions:       permissions,
	})
	zeroBytes(clientSecret)
	if err != nil {
		return ScopedToken{}, fmt.Errorf("%w: mint failed: %v", ErrScopedTokenUnavailable, err)
	}
	requiredUntil := s.now().Add(grant.MinTTL)
	if !result.ExpiresAt.After(requiredUntil) {
		return ScopedToken{}, fmt.Errorf("%w: minted token expires before min_ttl", ErrScopedTokenUnavailable)
	}
	issueID, err := newIssueID()
	if err != nil {
		return ScopedToken{}, err
	}
	permissionsJSON, err := json.Marshal(permissions)
	if err != nil {
		return ScopedToken{}, err
	}
	issue := sqlite.TokenIssue{
		ID:                  issueID,
		GrantHash:           grant.GrantHash,
		AccountID:           grant.AccountID,
		TokenHash:           hashToken(result.Token),
		ExpiresAt:           result.ExpiresAt,
		PermissionsJSON:     string(permissionsJSON),
		RepositorySelection: result.RepositorySelection,
		IssuedAt:            s.now(),
	}
	if err := s.store.SaveTokenIssue(ctx, issue); err != nil {
		return ScopedToken{}, err
	}
	if err := s.recordAudit(ctx, "token_scoped_minted", grant.AgentID, "token_issue", issueID, "success", ""); err != nil {
		return ScopedToken{}, err
	}
	return ScopedToken{GrantHash: grant.GrantHash, Token: result.Token, ExpiresAt: result.ExpiresAt, IssueID: issueID}, nil
}

func (s *Service) recordAudit(ctx context.Context, eventType, actorID, subjectType, subjectID, outcome, code string) error {
	return s.store.RecordAudit(ctx, sqlite.AuditEvent{
		Timestamp:   s.now(),
		EventType:   eventType,
		ActorType:   "agent",
		ActorID:     actorID,
		SubjectType: subjectType,
		SubjectID:   subjectID,
		Outcome:     outcome,
		Code:        code,
	})
}

func hashToken(token string) string {
	sum := sha256.Sum256([]byte(token))
	return hex.EncodeToString(sum[:])
}

func newIssueID() (string, error) {
	var raw [16]byte
	if _, err := rand.Read(raw[:]); err != nil {
		return "", fmt.Errorf("generate token issue id: %w", err)
	}
	return "tok_" + base64.RawURLEncoding.EncodeToString(raw[:]), nil
}

func zeroBytes(value []byte) {
	for i := range value {
		value[i] = 0
	}
}
