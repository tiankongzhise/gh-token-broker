#!/usr/bin/env python3
"""Small repository hygiene checks used both locally and in CI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".md", ".py", ".go", ".yaml", ".yml", ".json", ".html", ".js", ".css",
    ".svg", ".txt", ".gitignore", ".example",
}
SKIP_DIRS = {".git", "node_modules", "bin", "dist", "tmp", "temp", "coverage"}
CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")


def iter_repo_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(ROOT).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        yield path


def check_conflict_markers() -> list[str]:
    failures: list[str] = []
    for path in iter_repo_files():
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != ".gitignore":
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(lines, 1):
            if line.startswith(CONFLICT_MARKERS):
                failures.append(f"{path.relative_to(ROOT)}:{lineno}: conflict marker")
    return failures


def check_tracked_ignored_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-i", "-c", "--exclude-standard"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ["unable to run git ls-files for ignore hygiene"]
    return [f"tracked ignored file: {line}" for line in result.stdout.splitlines() if line]


def check_wireframe_svgs() -> list[str]:
    wireframes = ROOT / "design" / "wireframes"
    if not wireframes.exists():
        return []
    failures: list[str] = []
    svgs = sorted(wireframes.glob("*.svg"))
    if not svgs:
        failures.append("design/wireframes exists but contains no SVG files")
    for svg in svgs:
        try:
            ElementTree.parse(svg)
        except ElementTree.ParseError as exc:
            failures.append(f"{svg.relative_to(ROOT)}: invalid XML: {exc}")
    return failures


def main() -> int:
    failures = []
    failures.extend(check_conflict_markers())
    failures.extend(check_tracked_ignored_files())
    failures.extend(check_wireframe_svgs())
    if failures:
        print("repository hygiene check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("repository hygiene check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
