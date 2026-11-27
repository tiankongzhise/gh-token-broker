package version

import (
	"strings"
	"testing"
)

func TestStringIncludesVersionCommitAndBuildDate(t *testing.T) {
	oldVersion, oldCommit, oldBuildDate := Version, Commit, BuildDate
	defer func() { Version, Commit, BuildDate = oldVersion, oldCommit, oldBuildDate }()
	Version, Commit, BuildDate = "0.1.0-test", "abc123", "2026-11-27T00:00:00Z"
	out := String()
	for _, part := range []string{"gh-token-broker", "0.1.0-test", "abc123", "2026-11-27T00:00:00Z"} {
		if !strings.Contains(out, part) {
			t.Fatalf("version output missing %q: %q", part, out)
		}
	}
}
