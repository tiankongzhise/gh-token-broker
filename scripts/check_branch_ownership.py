#!/usr/bin/env python3
"""Validate branch file ownership against docs/branch-ownership.json."""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "branch-ownership.json"


def run(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def match(path: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(path, pattern) or (pattern.endswith("/**") and path == pattern[:-3])


def overlaps(a: str, b: str) -> bool:
    if a == b:
        return True
    for x, y in ((a, b), (b, a)):
        if x.endswith("/**"):
            prefix = x[:-3]
            if y == prefix or y.startswith(prefix.rstrip("/") + "/") or (y.endswith("/**") and y[:-3].startswith(prefix.rstrip("/") + "/")):
                return True
    return False


def main() -> int:
    failures: list[str] = []
    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"branch ownership registry unreadable: {exc}")
        return 1

    branches = registry.get("branches", {})
    active = {name: cfg for name, cfg in branches.items() if cfg.get("status") == "active"}

    owners = list(active.items())
    for i, (left, lcfg) in enumerate(owners):
        for right, rcfg in owners[i + 1 :]:
            for lp in lcfg.get("write", []):
                for rp in rcfg.get("write", []):
                    if overlaps(lp, rp):
                        failures.append(f"overlapping active ownership: {left}:{lp} vs {right}:{rp}")

    branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or run("branch", "--show-current")
    try:
        base = os.environ.get("GITHUB_BASE_REF", "main")
        base_ref = f"origin/{base}"
        run("rev-parse", "--verify", base_ref)
        changed = run("diff", "--name-only", f"{base_ref}...HEAD").splitlines()
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"branch ownership check failed: cannot inspect base diff: {exc}")
        return 1

    own_patterns = active.get(branch, {}).get("write", [])
    exceptions = {
        item.get("path")
        for item in registry.get("exceptions", [])
        if item.get("branch") == branch
    }
    other_owned: dict[str, str] = {}
    for name, cfg in active.items():
        if name == branch:
            continue
        for pattern in cfg.get("write", []):
            other_owned[pattern] = name

    for path in [p for p in changed if p]:
        if any(match(path, pattern) for pattern in own_patterns) or path in exceptions:
            continue
        for pattern, owner in other_owned.items():
            if match(path, pattern):
                failures.append(f"{branch}: {path} is owned by {owner} ({pattern})")
                break
        else:
            if branch.startswith("feat/"):
                failures.append(f"{branch}: {path} is outside registered feature ownership")

    if branch.startswith("feat/") and branch not in active:
        failures.append(f"{branch}: active feature branch is not registered in branch-ownership.json")

    if failures:
        print("branch ownership check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("branch ownership check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
