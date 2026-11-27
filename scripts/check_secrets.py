#!/usr/bin/env python3
"""Baseline secret scanner for pre-push checks.

The scanner intentionally reports only the finding type, origin, path, and line
number. It never prints the matched secret value.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "GitHub classic PAT": re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    "GitHub fine-grained PAT": re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    "GitHub OAuth access token": re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    "GitHub App user access token": re.compile(r"ghu_[A-Za-z0-9_]{20,}"),
    "GitHub App refresh token": re.compile(r"ghr_[A-Za-z0-9_]{20,}"),
    "GitHub App installation token": re.compile(r"ghs_[A-Za-z0-9_]{20,}"),
    "private key block": re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    "AWS access key id": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    "GitLab PAT": re.compile(r"glpat-[A-Za-z0-9_-]{20,}"),
    "OpenAI-style API key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "JWT-like bearer token": re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
}

BINARY_PROBE_SIZE = 4096
MAX_FILE_SIZE = 5 * 1024 * 1024


def run_git(root: Path, args: list[str], *, text: bool = True) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args],
        text=text,
        stderr=subprocess.DEVNULL,
    )


def repo_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return Path(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def decode_secret_text(data: bytes) -> str | None:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError:
            return None

    probe = data[:BINARY_PROBE_SIZE]
    if b"\x00" in probe:
        return None

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="ignore")


def scan_text(text: str, origin: str, path: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for finding_type, pattern in SECRET_PATTERNS.items():
            if pattern.search(line):
                findings.append(
                    {
                        "type": finding_type,
                        "origin": origin,
                        "path": path,
                        "line": str(line_number),
                    }
                )
    return findings


def scan_bytes(data: bytes, origin: str, path: str) -> list[dict[str, str]]:
    if len(data) > MAX_FILE_SIZE:
        return []
    text = decode_secret_text(data)
    if text is None:
        return []
    return scan_text(text, origin, path)


def iter_history_blobs(root: Path):
    try:
        object_listing = run_git(root, ["rev-list", "--objects", "--all", "HEAD"])
    except subprocess.CalledProcessError:
        return

    blob_paths: dict[str, set[str]] = defaultdict(set)
    for line in object_listing.splitlines():
        if not line.strip():
            continue
        object_id, separator, path = line.partition(" ")
        blob_paths[object_id].add(path if separator else "<unknown>")

    for object_id, paths in sorted(blob_paths.items()):
        try:
            object_type = run_git(root, ["cat-file", "-t", object_id]).strip()
        except subprocess.CalledProcessError:
            continue
        if object_type != "blob":
            continue
        try:
            data = subprocess.check_output(
                ["git", "-C", str(root), "cat-file", "blob", object_id],
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            continue
        for path in sorted(paths):
            yield object_id, path, data


def scan_history(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for _object_id, path, data in iter_history_blobs(root):
        findings.extend(scan_bytes(data, "git-history", path))
    return findings


def scan_worktree(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    try:
        listing = run_git(root, ["ls-files", "-co", "--exclude-standard"])
    except subprocess.CalledProcessError:
        return findings

    for relative_path in listing.splitlines():
        if not relative_path:
            continue
        path = root / relative_path
        try:
            if not path.is_file() or path.stat().st_size > MAX_FILE_SIZE:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        findings.extend(scan_bytes(data, "worktree", relative_path))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan repository content for common secret patterns.")
    parser.add_argument("--history-only", action="store_true", help="scan only committed git history")
    parser.add_argument("--worktree-only", action="store_true", help="scan only the current worktree")
    args = parser.parse_args()

    root = repo_root()
    findings: list[dict[str, str]] = []

    scan_history_enabled = not args.worktree_only
    scan_worktree_enabled = not args.history_only

    if scan_history_enabled:
        findings.extend(scan_history(root))
    if scan_worktree_enabled:
        findings.extend(scan_worktree(root))

    unique_findings = {
        (item["type"], item["origin"], item["path"], item["line"]): item for item in findings
    }

    if unique_findings:
        print("secret scan failed; potential secret material found:", file=sys.stderr)
        for item in sorted(unique_findings.values(), key=lambda x: (x["origin"], x["path"], x["line"], x["type"])):
            print(
                f"  {item['origin']}:{item['path']}:{item['line']}: {item['type']}",
                file=sys.stderr,
            )
        print("remove or rotate the affected secret before pushing; matched values were not printed", file=sys.stderr)
        return 1

    print("secret scan passed: no known secret patterns found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
