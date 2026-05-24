"""Apply GitHub API mutations: comments, bio, gists, profile README."""
from __future__ import annotations

import base64

import httpx

from vibecheck.findings import Finding
from vibecheck.github_client import GitHubClient


def apply_github_api_fix(finding: Finding, client: GitHubClient) -> None:
    payload = finding.fix_payload
    action = payload.get("action")

    if action == "update_comment":
        comment = client.get(payload["comment_url"]) or {}
        body = (comment.get("body") or "").replace(payload["find"], payload.get("replace", ""))
        path = payload["comment_url"].split("api.github.com")[-1]
        client.patch(path, json={"body": body})
        return

    if action == "update_bio":
        # For bio updates, send the replacement value directly. The caller has already
        # decided the new text via the find/replace pair, no need to GET first.
        # If the user wants to rephrase rather than wipe, callers should supply replace.
        client.patch("/user", json={"bio": payload.get("replace", "")})
        return

    if action == "update_gist_description":
        gist_id = payload["gist_id"]
        gist = client.get(f"/gists/{gist_id}") or {}
        desc = (gist.get("description") or "").replace(payload["find"], payload.get("replace", ""))
        client.patch(f"/gists/{gist_id}", json={"description": desc})
        return

    if action == "update_gist_file":
        gist_id = payload["gist_id"]
        filename = payload["filename"]
        gist = client.get(f"/gists/{gist_id}") or {}
        old = (gist.get("files") or {}).get(filename, {}).get("content", "")
        new = old.replace(payload["find"], payload.get("replace", ""))
        client.patch(f"/gists/{gist_id}", json={"files": {filename: {"content": new}}})
        return

    if action == "update_profile_readme":
        user = payload["user"]
        readme = client.get(f"/repos/{user}/{user}/contents/README.md")
        if not readme:
            return
        old = base64.b64decode(readme["content"]).decode("utf-8", errors="replace")
        new = old.replace(payload["find"], payload.get("replace", ""))
        encoded = base64.b64encode(new.encode("utf-8")).decode("ascii")
        # GitHub's contents endpoint uses PUT to update file contents.
        url = f"https://api.github.com/repos/{user}/{user}/contents/README.md"
        httpx.put(url, headers=client._headers(), json={
            "message": "chore: update profile README",
            "content": encoded,
            "sha": readme["sha"],
        }, timeout=30)
