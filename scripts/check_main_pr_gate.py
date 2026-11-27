#!/usr/bin/env python3
"""Block feature branches while unrelated open pull requests target main."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_BRANCH = "main"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def current_branch() -> str:
    return os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or git("branch", "--show-current")


def repository_slug() -> str | None:
    if os.environ.get("GITHUB_REPOSITORY"):
        return os.environ["GITHUB_REPOSITORY"]
    try:
        remote = git("config", "--get", "remote.origin.url")
    except (subprocess.CalledProcessError, OSError):
        return None
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$", remote)
    if not match:
        return None
    return f"{match.group('owner')}/{match.group('repo')}"


def api_json(url: str, token: str | None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "gh-token-broker-main-pr-gate",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def open_pull_requests(repo: str, token: str | None) -> list[dict]:
    api_base = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    pulls: list[dict] = []
    for page in range(1, 11):
        query = urllib.parse.urlencode({"state": "open", "per_page": "100", "page": str(page)})
        batch = api_json(f"{api_base}/repos/{repo}/pulls?{query}", token)
        if not isinstance(batch, list):
            raise RuntimeError("GitHub pulls API returned a non-list response")
        pulls.extend(batch)
        if len(batch) < 100:
            break
    return pulls


def is_own_main_pr(pr: dict, branch: str, repo: str) -> bool:
    head = pr.get("head") or {}
    head_repo = head.get("repo") or {}
    return head.get("ref") == branch and head_repo.get("full_name") == repo


def main() -> int:
    try:
        branch = current_branch()
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"main PR gate check failed: cannot determine current branch: {exc}")
        return 1

    if not branch.startswith("feat/"):
        print(f"main PR gate check passed: {branch} is not a feature branch")
        return 0

    repo = repository_slug()
    if not repo:
        print("main PR gate check failed: cannot determine GitHub repository slug")
        return 1

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        pulls = open_pull_requests(repo, token)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError, json.JSONDecodeError, OSError) as exc:
        if os.environ.get("CI") == "true":
            print(f"main PR gate check failed: cannot query open pull requests in CI: {exc}")
            return 1
        print(f"main PR gate warning: cannot query open pull requests locally ({exc}); CI remains authoritative")
        return 0

    blocking: list[str] = []
    for pr in pulls:
        base = pr.get("base") or {}
        if base.get("ref") != MAIN_BRANCH:
            continue
        if is_own_main_pr(pr, branch, repo):
            continue
        head = pr.get("head") or {}
        blocking.append(f"#{pr.get('number')} {pr.get('title')!r} ({head.get('ref')} -> {base.get('ref')})")

    if blocking:
        print("main PR gate check failed: open pull requests targeting main must be handled before feature work continues:")
        for item in blocking:
            print(f"- {item}")
        print("feature branches may resume only after those PRs are merged or closed, main CI is green, and the feature branch is synchronized")
        return 1

    print(f"main PR gate check passed: no unrelated open pull requests target {MAIN_BRANCH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
