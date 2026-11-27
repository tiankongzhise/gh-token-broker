#!/usr/bin/env python3
"""Validate project commit message structure for commits being integrated."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TYPES = {"feat", "fix", "docs", "chore", "ci", "test", "refactor", "perf", "build", "revert"}
HEADER_RE = re.compile(r"^(?P<type>[a-z]+)(?:\([a-z0-9][a-z0-9./-]*\))?!?: (?P<subject>.+)$")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
LOW_INFORMATION_SUBJECTS = {
    "update",
    "fix",
    "wip",
    "tmp",
    "misc",
    "更新",
    "修复",
    "修改",
    "更新文档",
    "修复问题",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def commit_range() -> str:
    base = os.environ.get("GITHUB_BASE_REF") or "main"
    return f"origin/{base}...HEAD"


def main() -> int:
    failures: list[str] = []
    rev_range = commit_range()
    try:
        hashes = [line for line in git("rev-list", rev_range).splitlines() if line]
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"commit message check failed: cannot inspect {rev_range}: {exc}")
        return 1

    for sha in hashes:
        try:
            meta = git("show", "-s", "--format=%P%n%B", sha)
        except (subprocess.CalledProcessError, OSError) as exc:
            failures.append(f"{sha[:8]}: cannot read commit metadata: {exc}")
            continue
        lines = meta.splitlines()
        if not lines:
            failures.append(f"{sha[:8]}: empty commit message")
            continue
        parents = lines[0].split()
        message_lines = lines[1:]
        header = message_lines[0] if message_lines else ""
        if len(parents) > 1:
            continue

        match = HEADER_RE.fullmatch(header)
        if not match:
            failures.append(f"{sha[:8]}: header is not a valid Conventional Commit: {header!r}")
            continue
        ctype = match.group("type")
        subject = match.group("subject").strip()
        if ctype not in TYPES:
            failures.append(f"{sha[:8]}: unsupported commit type {ctype!r}")
        if not subject:
            failures.append(f"{sha[:8]}: empty Chinese subject")
        if len(subject) > 72:
            failures.append(f"{sha[:8]}: subject exceeds 72 characters")
        if not CJK_RE.search(subject):
            failures.append(f"{sha[:8]}: subject must use Chinese semantic text")
        if subject.lower() in LOW_INFORMATION_SUBJECTS or subject in LOW_INFORMATION_SUBJECTS:
            failures.append(f"{sha[:8]}: low-information subject {subject!r}")
        if subject.endswith(("。", ".")):
            failures.append(f"{sha[:8]}: subject must not end with a period")

        body_lines = [line.strip() for line in message_lines[1:] if line.strip()]
        if len(body_lines) < 2:
            failures.append(f"{sha[:8]}: body must contain at least two non-empty information lines")
        if not any("验证：" in line or line.startswith("验证:") for line in body_lines):
            failures.append(f"{sha[:8]}: body must include a '验证：' line")
        if not CJK_RE.search("\n".join(body_lines)):
            failures.append(f"{sha[:8]}: body must use Chinese semantic text")

    if failures:
        print("commit message check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"commit message check passed: {len(hashes)} commit(s) in {rev_range}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
