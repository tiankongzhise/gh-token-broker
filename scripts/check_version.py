#!/usr/bin/env python3
"""Validate the repository VERSION file and release tag consistency."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = ROOT / "VERSION"
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def split_version(value: str) -> tuple[str, str | None, str | None]:
    without_build, sep, build = value.partition("+")
    core, dash, prerelease = without_build.partition("-")
    return core, prerelease if dash else None, build if sep else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="release tag to compare with VERSION; defaults to GitHub tag context when present")
    parser.add_argument("--require-release", action="store_true", help="require VERSION to have no prerelease suffix")
    args = parser.parse_args()

    failures: list[str] = []
    try:
        raw = VERSION.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"version check failed: cannot read VERSION: {exc}")
        return 1

    lines = raw.splitlines()
    if len(lines) != 1 or not raw.endswith("\n") or lines[0] != lines[0].strip():
        failures.append("VERSION must contain exactly one newline-terminated version line")
    version = raw.strip()
    match = SEMVER_RE.fullmatch(version)
    if not match:
        failures.append(f"VERSION is not valid Semantic Versioning 2.0.0: {version!r}")

    _core, prerelease, _build = split_version(version)
    if args.require_release and prerelease:
        failures.append(f"release builds must not use a prerelease VERSION: {version}")
    is_dev = bool(prerelease and prerelease.split(".")[0] == "dev")

    tag = args.tag
    if not tag and os.environ.get("GITHUB_REF_TYPE") == "tag":
        tag = os.environ.get("GITHUB_REF_NAME", "")
    if tag:
        if not tag.startswith("v"):
            failures.append(f"release tag must use v prefix: {tag}")
        tag_version = tag[1:] if tag.startswith("v") else tag
        if not SEMVER_RE.fullmatch(tag_version):
            failures.append(f"release tag is not valid v-prefixed SemVer: {tag}")
        elif tag_version != version:
            failures.append(f"release tag {tag} does not match VERSION {version}")
        if is_dev:
            failures.append(f"development VERSION {version} must not be tagged as a release")

    if failures:
        print("version check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"version check passed: {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
