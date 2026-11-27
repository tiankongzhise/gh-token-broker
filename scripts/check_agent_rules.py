#!/usr/bin/env python3
"""Validate the layered agent-rules registry and domain rule files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "agent-rules" / "registry.json"
OWNERSHIP = ROOT / "docs" / "branch-ownership.json"
ALLOWED_STATUSES = {"active", "inactive"}


def overlaps(a: str, b: str) -> bool:
    if a == b:
        return True
    for x, y in ((a, b), (b, a)):
        if x.endswith("/**"):
            prefix = x[:-3].rstrip("/")
            if y == prefix or y.startswith(prefix + "/") or (y.endswith("/**") and y[:-3].rstrip("/").startswith(prefix + "/")):
                return True
    return False


def main() -> int:
    failures: list[str] = []
    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        ownership = json.loads(OWNERSHIP.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"agent rules check failed: cannot read registry: {exc}")
        return 1

    domains = registry.get("domains", [])
    ids = [domain.get("id") for domain in domains]
    if len(ids) != len(set(ids)):
        failures.append("duplicate domain id in agent-rules registry")

    active_domains = []
    branches = ownership.get("branches", {})
    for domain in domains:
        did = domain.get("id", "<missing id>")
        status = domain.get("status")
        if status not in ALLOWED_STATUSES:
            failures.append(f"{did}: unsupported domain status {status!r}")
        rel_file = domain.get("file", "")
        path = ROOT / rel_file
        if not rel_file.startswith("docs/agent-rules/") or not path.exists():
            failures.append(f"{did}: missing or invalid domain rule file {rel_file!r}")
        if not isinstance(domain.get("branches", []), list) or not isinstance(domain.get("paths", []), list):
            failures.append(f"{did}: branches and paths must be lists")
            continue
        if status == "active":
            active_domains.append(domain)
        for branch in domain.get("branches", []):
            branch_status = branches.get(branch, {}).get("status")
            if status == "active" and branch_status != "active":
                failures.append(f"{did}: active domain references non-active branch {branch} ({branch_status!r})")
            if branch_status == "active":
                registered = set(domain.get("paths", []))
                owned = set(branches[branch].get("write", []))
                if registered != owned:
                    failures.append(f"{did}: paths do not match active ownership for {branch}")

    for i, left in enumerate(active_domains):
        for right in active_domains[i + 1 :]:
            for lp in left.get("paths", []):
                for rp in right.get("paths", []):
                    if overlaps(lp, rp):
                        failures.append(f"overlapping active domain paths: {left.get('id')}:{lp} vs {right.get('id')}:{rp}")

    if failures:
        print("agent rules check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("agent rules check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
