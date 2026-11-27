#!/usr/bin/env python3
"""Require decision evidence when existing AGENTS.md constraint lines are mutated."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = "AGENTS.md"
DECISIONS = "docs/DECISIONS.md"
DECISION_RE = re.compile(r"D-\d{4}")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8")


def unified_diff(base_ref: str, path: str) -> str:
    return git("diff", "--unified=0", f"{base_ref}...HEAD", "--", path)


def meaningful_removed_lines(diff_text: str) -> list[str]:
    removed: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("---") or line.startswith("@@"):
            continue
        if line.startswith("-"):
            content = line[1:].strip()
            if content:
                removed.append(content)
    return removed


def added_lines(diff_text: str) -> list[str]:
    return [line[1:] for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")]


def main() -> int:
    base = os.environ.get("GITHUB_BASE_REF") or "main"
    base_ref = f"origin/{base}"
    try:
        agents_diff = unified_diff(base_ref, AGENTS)
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"AGENTS mutation check failed: cannot inspect AGENTS diff: {exc}")
        return 1

    removed = meaningful_removed_lines(agents_diff)
    if not removed:
        print("AGENTS mutation check passed: no existing AGENTS.md constraint lines were removed or rewritten")
        return 0

    try:
        decisions_diff = unified_diff(base_ref, DECISIONS)
        commit_messages = git("log", "--format=%B", f"{base_ref}..HEAD")
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"AGENTS mutation check failed: cannot inspect decision evidence: {exc}")
        return 1

    additions = added_lines(decisions_diff)
    agents_decision_ids = {
        match
        for line in additions
        if "agents.md" in line.lower() or "agents 约束" in line.lower()
        for match in DECISION_RE.findall(line)
    }
    committed_ids = set(DECISION_RE.findall(commit_messages))
    evidenced_ids = agents_decision_ids & committed_ids

    failures: list[str] = []
    if not agents_decision_ids:
        failures.append("docs/DECISIONS.md must add decision evidence that explicitly covers the AGENTS.md mutation")
    if not evidenced_ids:
        failures.append("at least one commit must reference the D-xxxx decision covering the AGENTS.md mutation")

    if failures:
        print("AGENTS mutation check failed: existing AGENTS.md lines were removed or rewritten without sufficient recorded evidence:")
        print(f"- mutated/removed non-empty lines detected: {len(removed)}")
        for failure in failures:
            print(f"- {failure}")
        print("pure additions are allowed; mutation of existing constraints requires explicit user-approved decision evidence")
        return 1

    print(f"AGENTS mutation check passed: mutation evidence references {', '.join(sorted(evidenced_ids))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
