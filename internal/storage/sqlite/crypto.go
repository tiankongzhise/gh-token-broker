package sqlite

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"errors"
	"fmt"
)

const (
	masterKeySize = 32
	nonceSize     = 12
	keyVersion    = 1
)

func encryptSecret(masterKey, plaintext, associatedData []byte) (ciphertext, nonce []byte, err error) {
	if len(masterKey) != masterKeySize {
		return nil, nil, fmt.Errorf("master key has invalid length %d", len(masterKey))
	}
	block, err := aes.NewCipher(masterKey)
	if err != nil {
		return nil, nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, nil, err
	}
	nonce = make([]byte, nonceSize)
	if _, err := rand.Read(nonce); err != nil {
		return nil, nil, err
	}
	ciphertext = gcm.Seal(nil, nonce, plaintext, associatedData)
	return ciphertext, nonce, nil
}

func decryptSecret(masterKey, ciphertext, nonce, associatedData []byte) ([]byte, error) {
	if len(masterKey) != masterKeySize {
		return nil, fmt.Errorf("master key has invalid length %d", len(masterKey))
	}
	if len(nonce) != nonceSize {
		return nil, errors.New("invalid secret nonce length")
	}
	block, err := aes.NewCipher(masterKey)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	plaintext, err := gcm.Open(nil, nonce, ciphertext, associatedData)
	if err != nil {
		return nil, errors.New("secret authentication failed")
	}
	return plaintext, nil
}

func secretAssociatedData(ref, kind string, version int) []byte {
	return []byte(fmt.Sprintf("gh-token-broker:v1:%d:%s:%s", version, kind, ref))
}

func zeroizeBytes(value []byte) {
	for i := range value {
		value[i] = 0
	}
}
