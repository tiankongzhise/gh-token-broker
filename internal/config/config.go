package config

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

const SecretBackendEncryptedSQLiteWithWCMMasterKey = "encrypted-sqlite-with-wcm-master-key"

type Config struct {
	DatabasePath    string       `yaml:"database_path"`
	SecretBackend   string       `yaml:"secret_backend"`
	MasterKeyTarget string       `yaml:"master_key_target"`
	GitHub          GitHubConfig `yaml:"github"`
	Token           TokenConfig  `yaml:"token"`
}

type GitHubConfig struct {
	Host            string `yaml:"host"`
	BaseURL         string `yaml:"base_url"`
	APIBaseURL      string `yaml:"api_base_url"`
	ClientSecretRef string `yaml:"client_secret_ref"`
}

type TokenConfig struct {
	ParentRefreshSkew string `yaml:"parent_refresh_skew"`
}

func Default() Config {
	return Config{
		DatabasePath:    "gh-token-broker.db",
		SecretBackend:   SecretBackendEncryptedSQLiteWithWCMMasterKey,
		MasterKeyTarget: "gh-token-broker/master-key",
		GitHub: GitHubConfig{
			Host:            "github.com",
			BaseURL:         "https://github.com",
			APIBaseURL:      "https://api.github.com",
			ClientSecretRef: "github/app-client-secret",
		},
		Token: TokenConfig{
			ParentRefreshSkew: "10m",
		},
	}
}

func Load(path string) (Config, error) {
	cfg := Default()
	data, err := os.ReadFile(path)
	if err != nil {
		return Config{}, fmt.Errorf("read config: %w", err)
	}
	decoder := yaml.NewDecoder(bytes.NewReader(data))
	decoder.KnownFields(true)
	if err := decoder.Decode(&cfg); err != nil {
		return Config{}, fmt.Errorf("parse config: %w", err)
	}
	if err := cfg.Validate(); err != nil {
		return Config{}, err
	}
	return cfg, nil
}

func (c Config) Validate() error {
	if c.DatabasePath == "" {
		return errors.New("database_path is required")
	}
	if c.SecretBackend != SecretBackendEncryptedSQLiteWithWCMMasterKey {
		return fmt.Errorf("unsupported secret_backend %q", c.SecretBackend)
	}
	if c.MasterKeyTarget == "" {
		return errors.New("master_key_target is required")
	}
	if c.GitHub.Host == "" {
		return errors.New("github.host is required")
	}
	if c.GitHub.BaseURL == "" {
		return errors.New("github.base_url is required")
	}
	if c.GitHub.APIBaseURL == "" {
		return errors.New("github.api_base_url is required")
	}
	if c.GitHub.ClientSecretRef == "" {
		return errors.New("github.client_secret_ref is required")
	}
	if _, err := c.ParentSkew(); err != nil {
		return fmt.Errorf("token.parent_refresh_skew: %w", err)
	}
	return nil
}

func (c Config) ParentSkew() (time.Duration, error) {
	d, err := time.ParseDuration(c.Token.ParentRefreshSkew)
	if err != nil {
		return 0, err
	}
	if d < 0 {
		return 0, errors.New("must not be negative")
	}
	return d, nil
}
