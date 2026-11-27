package sqlite

import (
	"context"
	"crypto/rand"
	"errors"
	"fmt"
	"sync"
	"syscall"

	"github.com/danieljoos/wincred"

	"gh-token-broker/internal/platform/winmutex"
)

type KeyProvider interface {
	MasterKey(ctx context.Context) ([]byte, error)
}

type StaticKeyProvider struct {
	key []byte
}

func NewStaticKeyProvider(key []byte) (StaticKeyProvider, error) {
	if len(key) != masterKeySize {
		return StaticKeyProvider{}, fmt.Errorf("static master key must be %d bytes", masterKeySize)
	}
	copyKey := append([]byte(nil), key...)
	return StaticKeyProvider{key: copyKey}, nil
}

func (p StaticKeyProvider) MasterKey(context.Context) ([]byte, error) {
	return append([]byte(nil), p.key...), nil
}

type WCMKeyProvider struct {
	TargetName string

	mu  sync.Mutex
	key []byte
}

func NewWCMKeyProvider(targetName string) *WCMKeyProvider {
	return &WCMKeyProvider{TargetName: targetName}
}

func (p *WCMKeyProvider) MasterKey(context.Context) ([]byte, error) {
	p.mu.Lock()
	defer p.mu.Unlock()
	if len(p.key) == masterKeySize {
		return append([]byte(nil), p.key...), nil
	}
	if p.TargetName == "" {
		return nil, errors.New("windows credential target name is empty")
	}
	unlock, err := winmutex.Lock("master-key:" + p.TargetName)
	if err != nil {
		return nil, err
	}
	defer unlock()
	cred, err := wincred.GetGenericCredential(p.TargetName)
	if err == nil {
		if len(cred.CredentialBlob) != masterKeySize {
			return nil, fmt.Errorf("windows credential %q has invalid master key length", p.TargetName)
		}
		p.key = append([]byte(nil), cred.CredentialBlob...)
		return append([]byte(nil), p.key...), nil
	}
	if !errors.Is(err, syscall.ERROR_NOT_FOUND) {
		return nil, fmt.Errorf("read windows credential master key: %w", err)
	}
	key := make([]byte, masterKeySize)
	if _, err := rand.Read(key); err != nil {
		return nil, fmt.Errorf("generate master key: %w", err)
	}
	newCred := wincred.NewGenericCredential(p.TargetName)
	newCred.CredentialBlob = append([]byte(nil), key...)
	if err := newCred.Write(); err != nil {
		return nil, fmt.Errorf("write windows credential master key: %w", err)
	}
	p.key = key
	return append([]byte(nil), key...), nil
}
