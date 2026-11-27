package grant

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"time"

	"gh-token-broker/internal/storage/sqlite"
)

const (
	DefaultTTL     = 10 * time.Minute
	DefaultMaxUses = 1
	idPrefix       = "grt_"
)

var ErrInvalidGrantID = errors.New("invalid grant id")

type Store interface {
	CreateGrant(ctx context.Context, grant sqlite.Grant) error
	GetGrant(ctx context.Context, grantHash string) (sqlite.Grant, error)
	RedeemGrant(ctx context.Context, grantHash string, at time.Time) (sqlite.Grant, error)
	RevokeGrant(ctx context.Context, grantHash, reason string, at time.Time) error
	ExpireGrants(ctx context.Context, at time.Time) (int64, error)
}

type Service struct {
	store Store
	now   func() time.Time
}

type CreateInput struct {
	AgentID   string
	AccountID string
	Host      string
	Owner     string
	Repo      string
	Profile   string
	MinTTL    time.Duration
	TTL       time.Duration
	MaxUses   int
}

type CreatedGrant struct {
	ID    string
	Grant sqlite.Grant
}

func NewService(store Store) *Service {
	return &Service{store: store, now: func() time.Time { return time.Now().UTC() }}
}

func (s *Service) Create(ctx context.Context, input CreateInput) (CreatedGrant, error) {
	if input.AgentID == "" || input.AccountID == "" || input.Host == "" || input.Owner == "" || input.Repo == "" || input.Profile == "" {
		return CreatedGrant{}, errors.New("agent id, account id, host, owner, repo, and profile are required")
	}
	if input.MinTTL < time.Second {
		return CreatedGrant{}, errors.New("min_ttl must be at least one second")
	}
	if input.TTL <= 0 {
		input.TTL = DefaultTTL
	}
	if input.MaxUses <= 0 {
		input.MaxUses = DefaultMaxUses
	}
	id, hash, err := newID()
	if err != nil {
		return CreatedGrant{}, err
	}
	now := s.now()
	grant := sqlite.Grant{
		GrantHash: hash,
		AgentID:   input.AgentID,
		AccountID: input.AccountID,
		Host:      input.Host,
		Owner:     input.Owner,
		Repo:      input.Repo,
		Profile:   input.Profile,
		MinTTL:    input.MinTTL,
		ExpiresAt: now.Add(input.TTL),
		MaxUses:   input.MaxUses,
		Status:    sqlite.GrantStatusActive,
		CreatedAt: now,
	}
	if err := s.store.CreateGrant(ctx, grant); err != nil {
		return CreatedGrant{}, err
	}
	return CreatedGrant{ID: id, Grant: grant}, nil
}

func (s *Service) Redeem(ctx context.Context, id string) (sqlite.Grant, error) {
	hash, err := HashID(id)
	if err != nil {
		return sqlite.Grant{}, err
	}
	grant, err := s.store.RedeemGrant(ctx, hash, s.now())
	if errors.Is(err, sqlite.ErrGrantExpired) {
		_, _ = s.store.ExpireGrants(ctx, s.now())
	}
	return grant, err
}

func (s *Service) Revoke(ctx context.Context, id, reason string) error {
	hash, err := HashID(id)
	if err != nil {
		return err
	}
	return s.store.RevokeGrant(ctx, hash, reason, s.now())
}

func (s *Service) ExpireDue(ctx context.Context) (int64, error) {
	return s.store.ExpireGrants(ctx, s.now())
}

func HashID(id string) (string, error) {
	if len(id) <= len(idPrefix) || id[:len(idPrefix)] != idPrefix {
		return "", ErrInvalidGrantID
	}
	sum := sha256.Sum256([]byte(id))
	return hex.EncodeToString(sum[:]), nil
}

func newID() (string, string, error) {
	var raw [32]byte
	if _, err := rand.Read(raw[:]); err != nil {
		return "", "", fmt.Errorf("generate grant id: %w", err)
	}
	id := idPrefix + base64.RawURLEncoding.EncodeToString(raw[:])
	hash, err := HashID(id)
	if err != nil {
		return "", "", err
	}
	return id, hash, nil
}
