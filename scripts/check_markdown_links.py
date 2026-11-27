#!/usr/bin/env python3
"""Check that local Markdown links point to existing files.

This is intentionally small and conservative. It validates file existence only;
it does not render Markdown or validate anchors.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "#")
SKIP_DIRS = {".git", "node_modules", "bin", "dist", "tmp", "temp", "coverage"}


def markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        rel_parts = path.relative_to(ROOT).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        files.append(path)
    return sorted(files)


def main() -> int:
    missing: list[tuple[Path, str]] = []
    for md in markdown_files():
        text = md.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip().strip("<>")
            if target.startswith(SKIP_PREFIXES):
                continue
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            candidate = (md.parent / target).resolve()
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                missing.append((md.relative_to(ROOT), match.group(1)))
                continue
            if not candidate.exists():
                missing.append((md.relative_to(ROOT), match.group(1)))

    if missing:
        print("missing markdown link targets:")
        for file, target in missing:
            print(f"- {file}: {target}")
        return 1
    print(f"markdown link check passed: {len(markdown_files())} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
