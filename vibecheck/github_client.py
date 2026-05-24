"""Thin httpx wrapper around the GitHub REST API."""
from __future__ import annotations

import os
import re
import subprocess
from typing import Any

import httpx


GH_API = "https://api.github.com"


class GitHubError(RuntimeError):
    """Generic GitHub API error."""


class RateLimitError(GitHubError):
    """Raised when the GitHub API returns a rate-limit response."""

    def __init__(self, reset_epoch: int):
        super().__init__(f"GitHub API rate limit hit, resets at epoch {reset_epoch}")
        self.reset_epoch = reset_epoch


def _gh_cli_token() -> str | None:
    """Try `gh auth token` as a fallback when GITHUB_TOKEN is unset."""
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=5
        )
        if out.returncode == 0:
            t = out.stdout.strip()
            return t or None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


class GitHubClient:
    def __init__(self, token: str | None = None, base_url: str = GH_API):
        self.token = token or os.environ.get("GITHUB_TOKEN") or _gh_cli_token()
        self.base_url = base_url

    def _headers(self) -> dict[str, str]:
        h = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "vibecheck/0.1.0",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _check(self, resp: httpx.Response) -> None:
        if resp.status_code == 403 and resp.headers.get("x-ratelimit-remaining") == "0":
            reset = int(resp.headers.get("x-ratelimit-reset", "0"))
            raise RateLimitError(reset)
        if resp.status_code >= 500:
            raise GitHubError(f"GitHub server error {resp.status_code}")

    def get(self, path: str, params: dict | None = None) -> Any:
        url = path if path.startswith("http") else self.base_url + path
        resp = httpx.get(url, headers=self._headers(), params=params, timeout=30)
        if resp.status_code == 404:
            return None
        self._check(resp)
        resp.raise_for_status()
        return resp.json()

    def patch(self, path: str, json: dict) -> Any:
        url = self.base_url + path
        resp = httpx.patch(url, headers=self._headers(), json=json, timeout=30)
        self._check(resp)
        resp.raise_for_status()
        return resp.json()

    def paginated(self, path: str, params: dict | None = None) -> list[dict]:
        results: list[dict] = []
        page = 1
        merged = dict(params or {})
        merged["per_page"] = 100
        while True:
            merged["page"] = page
            url = self.base_url + path
            resp = httpx.get(url, headers=self._headers(), params=merged, timeout=30)
            if resp.status_code == 404:
                break
            self._check(resp)
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            results.extend(batch)
            link = resp.headers.get("link", "")
            if 'rel="next"' not in link:
                break
            page += 1
        return results
