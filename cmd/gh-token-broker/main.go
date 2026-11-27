package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"os"
	"time"

	"gh-token-broker/internal/config"
	"gh-token-broker/internal/githubapp"
	"gh-token-broker/internal/storage/sqlite"
	"gh-token-broker/internal/tokenchain"
)

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	if len(args) == 0 {
		usage()
		return errors.New("command is required")
	}
	switch args[0] {
	case "init":
		return runInit(args[1:])
	case "device-flow":
		return runDeviceFlow(args[1:])
	case "refresh-check":
		return runRefreshCheck(args[1:])
	case "help", "--help", "-h":
		usage()
		return nil
	default:
		usage()
		return fmt.Errorf("unknown command %q", args[0])
	}
}

func usage() {
	fmt.Fprint(os.Stderr, `gh-token-broker Phase 1 core token chain POC

Commands:
  init           initialize encrypted SQLite metadata and the WCM-backed master key
  device-flow    explicitly authorize one GitHub account through device flow
  refresh-check  verify the refresh chain without printing token material

No command prints access tokens, refresh tokens, client secrets, or master keys.
`)
}

func openConfiguredStore(configPath string) (*sqlite.Store, config.Config, error) {
	cfg, err := config.Load(configPath)
	if err != nil {
		return nil, config.Config{}, err
	}
	store, err := sqlite.Open(context.Background(), cfg.DatabasePath, sqlite.NewWCMKeyProvider(cfg.MasterKeyTarget))
	if err != nil {
		return nil, config.Config{}, err
	}
	return store, cfg, nil
}

func runInit(args []string) error {
	fs := flag.NewFlagSet("init", flag.ContinueOnError)
	configPath := fs.String("config", "config.yaml", "path to config YAML")
	if err := fs.Parse(args); err != nil {
		return err
	}
	store, _, err := openConfiguredStore(*configPath)
	if err != nil {
		return err
	}
	defer store.Close()
	fmt.Println("initialized encrypted SQLite store and master key provider")
	return nil
}

func runDeviceFlow(args []string) error {
	fs := flag.NewFlagSet("device-flow", flag.ContinueOnError)
	configPath := fs.String("config", "config.yaml", "path to config YAML")
	accountID := fs.String("account", "", "local account id")
	clientID := fs.String("client-id", "", "GitHub App client id")
	userLogin := fs.String("user-login", "", "expected GitHub user login metadata")
	offlineAccess := fs.Bool("offline-access", true, "request offline_access so GitHub returns an expiring user token and refresh token")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *accountID == "" || *clientID == "" {
		return errors.New("account and client-id are required")
	}
	store, cfg, err := openConfiguredStore(*configPath)
	if err != nil {
		return err
	}
	defer store.Close()
	skew, err := cfg.ParentSkew()
	if err != nil {
		return err
	}
	oauth := githubapp.New(cfg.GitHub.BaseURL)
	service := tokenchain.NewService(store, oauth, skew)
	var scopes []string
	if *offlineAccess {
		scopes = []string{"offline_access"}
	}
	ctx := context.Background()
	start, err := service.BeginDeviceFlow(ctx, *clientID, scopes)
	if err != nil {
		return err
	}
	fmt.Printf("open %s and enter user code %s\n", start.VerificationURI, start.UserCode)
	if start.VerificationURIComplete != "" {
		fmt.Printf("or open %s\n", start.VerificationURIComplete)
	}
	interval := time.Duration(positiveOrDefault(start.Interval, 5)) * time.Second
	deadline := time.Now().Add(time.Duration(positiveOrDefault(start.ExpiresIn, 900)) * time.Second)
	for {
		if time.Now().After(deadline) {
			return errors.New("device flow expired before authorization completed")
		}
		err := service.CompleteDeviceFlow(ctx, *accountID, cfg.GitHub.Host, *clientID, *userLogin, start.DeviceCode)
		if err == nil {
			fmt.Println("authorization stored; token material is encrypted and was not printed")
			return nil
		}
		var apiErr *githubapp.APIError
		if !errors.As(err, &apiErr) {
			return err
		}
		switch apiErr.Code {
		case "authorization_pending":
			time.Sleep(interval)
		case "slow_down":
			interval += 5 * time.Second
			time.Sleep(interval)
		default:
			return err
		}
	}
}

func runRefreshCheck(args []string) error {
	fs := flag.NewFlagSet("refresh-check", flag.ContinueOnError)
	configPath := fs.String("config", "config.yaml", "path to config YAML")
	accountID := fs.String("account", "", "local account id")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *accountID == "" {
		return errors.New("account is required")
	}
	store, cfg, err := openConfiguredStore(*configPath)
	if err != nil {
		return err
	}
	defer store.Close()
	skew, err := cfg.ParentSkew()
	if err != nil {
		return err
	}
	service := tokenchain.NewService(store, githubapp.New(cfg.GitHub.BaseURL), skew)
	token, err := service.EnsureParentToken(context.Background(), *accountID, 5*time.Minute)
	if err != nil {
		return err
	}
	fmt.Printf("refresh chain valid; parent token expires at %s (token not printed)\n", token.ExpiresAt.UTC().Format(time.RFC3339))
	return nil
}

func positiveOrDefault(value, fallback int) int {
	if value > 0 {
		return value
	}
	return fallback
}
