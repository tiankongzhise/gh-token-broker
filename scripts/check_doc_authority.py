#!/usr/bin/env python3
"""Validate the machine-readable documentation authority registry."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "authority-registry.json"


def authority_path(value: str) -> Path:
    return ROOT / value.split("#", 1)[0]


def main() -> int:
    failures: list[str] = []
    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"authority registry unreadable: {exc}")
        return 1

    records = registry.get("records", [])
    ids = [record.get("id") for record in records]
    if len(ids) != len(set(ids)):
        failures.append("duplicate record id in authority registry")

    for record in records:
        rid = record.get("id", "<missing id>")
        for key in ("authority", "currentState"):
            value = record.get(key)
            if not value:
                continue
            path = authority_path(value)
            if record.get("required", True) and not path.exists():
                failures.append(f"{rid}: missing authority file for {key}: {value}")

    rules = registry.get("rules", [])
    rule_ids = [rule.get("id") for rule in rules]
    if len(rule_ids) != len(set(rule_ids)):
        failures.append("duplicate rule id in authority registry")

    for rule in rules:
        rule_id = rule.get("id", "<missing rule id>")
        forbidden = rule.get("forbidden", [])
        required_any = rule.get("requiredAny", [])
        missing_ok = rule.get("missingOk", False)
        for rel in rule.get("paths", []):
            path = ROOT / rel
            if not path.exists():
                if missing_ok:
                    continue
                failures.append(f"{rule_id}: missing target {rel}")
                continue
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                if phrase in text:
                    failures.append(f"{rule_id}: {rel} contains forbidden stale phrase: {phrase}")
            if required_any and not any(phrase in text for phrase in required_any):
                failures.append(f"{rule_id}: {rel} lacks required authority reference")

    if failures:
        print("documentation authority check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("documentation authority check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
