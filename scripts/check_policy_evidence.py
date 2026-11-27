#!/usr/bin/env python3
"""Require explicit decision evidence for high-friction governance policies."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / "AGENTS.md", ROOT / "docs" / "GIT_GOVERNANCE.md"]
HIGH_FRICTION_TERMS = ("每次单独询问", "逐次确认", "每次确认")
DECISION_RE = re.compile(r"D-\d{4}")


def declares_policy(line: str) -> bool:
    stripped = line.strip()
    return "当前约定" in stripped or re.match(r">?\s*约定：", stripped) is not None


def policy_line_failure(path: str, line_number: int, line: str) -> str | None:
    if not declares_policy(line):
        return None
    term = next((term for term in HIGH_FRICTION_TERMS if term in line), None)
    if term and not DECISION_RE.search(line):
        return f"{path}:{line_number}: high-friction policy term {term!r} lacks explicit decision evidence (D-xxxx)"
    return None


def main() -> int:
    failures: list[str] = []
    for path in TARGETS:
        rel = path.relative_to(ROOT).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            failures.append(f"{rel}: cannot read policy file: {exc}")
            continue
        for line_number, line in enumerate(lines, start=1):
            failure = policy_line_failure(rel, line_number, line)
            if failure:
                failures.append(failure)

    if failures:
        print("policy evidence check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("policy evidence check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
