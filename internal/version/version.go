package version

import "fmt"

var (
	Version   = "dev"
	Commit    = "unknown"
	BuildDate = "unknown"
)

func String() string {
	return fmt.Sprintf("gh-token-broker %s (commit %s, built %s)", Version, Commit, BuildDate)
}
