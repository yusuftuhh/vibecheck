"""Enumerate all resources owned by a user and produce findings."""
from __future__ import annotations

import base64
from dataclasses import dataclass, field

import httpx

from vibecheck.config import Config
from vibecheck.findings import Finding
from vibecheck.github_client import GitHubClient
from vibecheck.scanners.text_patterns import scan_text
from vibecheck.targets import ProfileTarget, RemoteRepoTarget


@dataclass
class ProfileInventory:
    findings: list[Finding] = field(default_factory=list)
    repo_targets: list[RemoteRepoTarget] = field(default_factory=list)


def scan_profile(target: ProfileTarget, client: GitHubClient, config: Config) -> ProfileInventory:
    inv = ProfileInventory()

    user_info = client.get(f"/users/{target.user}") or {}
    bio = user_info.get("bio") or ""
    if bio:
        bio_findings = scan_text(bio, source=f"github.com/{target.user} bio", config=config)
        for f in bio_findings:
            f.category = "bio"
            f.fixer = "github_api"
            f.fix_payload = {"action": "update_bio", "user": target.user,
                             "find": f.fix_payload.get("find"), "replace": f.fix_payload.get("replace")}
        inv.findings.extend(bio_findings)

    repos = client.paginated(f"/users/{target.user}/repos")
    for r in repos:
        full_name = r.get("full_name", "")
        if "/" not in full_name:
            continue
        owner, repo = full_name.split("/", 1)
        if full_name in config.ignore_repos:
            continue
        inv.repo_targets.append(RemoteRepoTarget(owner=owner, repo=repo))

    gists = client.paginated(f"/users/{target.user}/gists")
    for g in gists:
        gist_id = g.get("id", "")
        desc = g.get("description") or ""
        if desc:
            for f in scan_text(desc, source=f"gist {gist_id} description", config=config):
                f.category = "gist"
                f.fixer = "github_api"
                f.fix_payload = {"action": "update_gist_description", "gist_id": gist_id,
                                 "find": f.fix_payload.get("find"), "replace": f.fix_payload.get("replace")}
                inv.findings.append(f)
        for filename, meta in (g.get("files") or {}).items():
            raw_url = meta.get("raw_url")
            if not raw_url:
                continue
            try:
                content = httpx.get(raw_url, timeout=30).text
            except httpx.HTTPError:
                continue
            for f in scan_text(content, source=f"gist {gist_id} file {filename}", config=config):
                f.category = "gist"
                f.fixer = "github_api"
                f.fix_payload = {"action": "update_gist_file", "gist_id": gist_id,
                                 "filename": filename,
                                 "find": f.fix_payload.get("find"), "replace": f.fix_payload.get("replace")}
                inv.findings.append(f)

    readme = client.get(f"/repos/{target.user}/{target.user}/contents/README.md")
    if readme and readme.get("encoding") == "base64":
        text = base64.b64decode(readme["content"]).decode("utf-8", errors="replace")
        for f in scan_text(text, source=f"github.com/{target.user} profile README", config=config):
            f.category = "profile_readme"
            f.fixer = "github_api"
            f.fix_payload = {"action": "update_profile_readme", "user": target.user,
                             "sha": readme.get("sha"),
                             "find": f.fix_payload.get("find"), "replace": f.fix_payload.get("replace")}
            inv.findings.append(f)

    return inv
