package config

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestLoadConfigAppliesDefaultsAndValidates(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config.yaml")
	data := []byte("database_path: test.db\n")
	if err := os.WriteFile(path, data, 0o600); err != nil {
		t.Fatal(err)
	}
	cfg, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.SecretBackend != SecretBackendEncryptedSQLiteWithWCMMasterKey {
		t.Fatalf("unexpected backend %q", cfg.SecretBackend)
	}
	if cfg.GitHub.Host != "github.com" || cfg.GitHub.BaseURL != "https://github.com" {
		t.Fatalf("unexpected github defaults: %+v", cfg.GitHub)
	}
	skew, err := cfg.ParentSkew()
	if err != nil {
		t.Fatal(err)
	}
	if skew != 10*time.Minute {
		t.Fatalf("unexpected parent skew %s", skew)
	}
}

func TestRejectsUnsupportedSecretBackend(t *testing.T) {
	cfg := Default()
	cfg.SecretBackend = "plaintext-test-only"
	if err := cfg.Validate(); err == nil {
		t.Fatalf("expected unsupported backend validation error")
	}
}

func TestRejectsUnknownConfigField(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config.yaml")
	data := []byte("database_path: test.db\nunknown_field: true\n")
	if err := os.WriteFile(path, data, 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := Load(path); err == nil {
		t.Fatalf("expected unknown field validation error")
	}
}
