"""Scan a user's comments across all repos via Search API."""
from __future__ import annotations

from vibecheck.config import Config
from vibecheck.findings import Finding
from vibecheck.github_client import GitHubClient
from vibecheck.scanners.text_patterns import scan_text


def _search_issues(client: GitHubClient, query: str) -> list[dict]:
    """Paginate /search/issues which returns {'items': [...], 'total_count': N}."""
    items: list[dict] = []
    page = 1
    while True:
        resp = client.get(
            "/search/issues",
            params={"q": query, "per_page": 100, "page": page},
        )
        if not resp:
            break
        batch = resp.get("items", []) if isinstance(resp, dict) else []
        if not batch:
            break
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items


def scan_user_comments(user: str, client: GitHubClient, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    search = _search_issues(client, f"commenter:{user}")
    seen_threads: set[str] = set()
    for item in search:
        comments_url = item.get("comments_url")
        html_url = item.get("html_url", "")
        if not comments_url or comments_url in seen_threads:
            continue
        seen_threads.add(comments_url)
        comments = client.get(comments_url) or []
        for c in comments:
            if (c.get("user") or {}).get("login") != user:
                continue
            body = c.get("body") or ""
            for f in scan_text(body, source=html_url, config=config):
                f.category = "comment"
                f.fixer = "github_api"
                f.fix_payload = {
                    "action": "update_comment",
                    "comment_url": comments_url.rsplit("/", 1)[0] + f"/{c['id']}",
                    "comment_id": c.get("id"),
                    "find": f.fix_payload.get("find"),
                    "replace": f.fix_payload.get("replace"),
                }
                findings.append(f)
    return findings
