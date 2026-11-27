package secretstore

import "context"

type Store interface {
	PutSecret(ctx context.Context, ref, kind string, plaintext []byte) error
	GetSecret(ctx context.Context, ref string) ([]byte, error)
}
