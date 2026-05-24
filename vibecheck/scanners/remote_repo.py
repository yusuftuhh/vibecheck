"""Scan a remote GitHub repo via the API."""
from __future__ import annotations

import fnmatch
import re

from vibecheck.config import Config
from vibecheck.findings import Finding, generate_id
from vibecheck.github_client import GitHubClient
from vibecheck.targets import RemoteRepoTarget


def scan_remote_repo(target: RemoteRepoTarget, client: GitHubClient, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_scan_commits(target, client, config))
    findings.extend(_scan_branches(target, client, config))
    findings.extend(_scan_tree(target, client, config))
    return findings


def _scan_commits(target: RemoteRepoTarget, client: GitHubClient, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    commits = client.paginated(f"/repos/{target.owner}/{target.repo}/commits")
    for commit in commits:
        sha = commit.get("sha", "")
        info = commit.get("commit", {})
        email = (info.get("author") or {}).get("email", "") or ""
        message = info.get("message", "") or ""

        for pat in config.bot_email_patterns:
            if pat in email:
                findings.append(
                    Finding(
                        id=generate_id("commit_author", f"{target.owner}/{target.repo}/{sha}", email),
                        severity="critical",
                        category="commit_author",
                        source=f"{target.owner}/{target.repo} commit {sha[:8]}",
                        snippet=email,
                        suggested_fix="rewrite commit author (requires force-push)",
                        fixer="git_history",
                        fix_payload={"owner": target.owner, "repo": target.repo, "sha": sha, "field": "author"},
                    )
                )
                break

        for line in message.splitlines():
            if re.match(r"(?i)co-authored-by:.*(claude|anthropic|copilot|gpt|openai)", line):
                findings.append(
                    Finding(
                        id=generate_id("commit_message", f"{target.owner}/{target.repo}/{sha}", line),
                        severity="critical",
                        category="commit_message",
                        source=f"{target.owner}/{target.repo} commit {sha[:8]}",
                        snippet=line.strip(),
                        suggested_fix="strip line via filter-branch + force-push",
                        fixer="git_history",
                        fix_payload={"owner": target.owner, "repo": target.repo, "sha": sha,
                                     "strip_line_match": line.strip()},
                    )
                )
    return findings


def _scan_branches(target: RemoteRepoTarget, client: GitHubClient, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    branches = client.paginated(f"/repos/{target.owner}/{target.repo}/branches")
    for b in branches:
        name = b.get("name", "")
        for pattern in config.branch_patterns:
            if re.match(pattern, name):
                findings.append(
                    Finding(
                        id=generate_id("branch_name", f"{target.owner}/{target.repo}", name),
                        severity="warning",
                        category="branch_name",
                        source=f"{target.owner}/{target.repo} branch {name}",
                        snippet=name,
                        suggested_fix="delete branch via API",
                        fixer="github_api",
                        fix_payload={"action": "delete_branch", "owner": target.owner,
                                     "repo": target.repo, "branch": name},
                    )
                )
                break
    return findings


def _scan_tree(target: RemoteRepoTarget, client: GitHubClient, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    tree = client.get(f"/repos/{target.owner}/{target.repo}/git/trees/HEAD", params={"recursive": "1"})
    if not tree:
        return findings
    for entry in tree.get("tree", []):
        if entry.get("type") != "blob":
            continue
        path = entry.get("path", "")
        for pattern in config.file_paths:
            matched = (pattern.endswith("/") and path.startswith(pattern)) or \
                      ("*" in pattern and fnmatch.fnmatch(path, pattern)) or \
                      (path == pattern)
            if matched:
                findings.append(
                    Finding(
                        id=generate_id("tracked_file", f"{target.owner}/{target.repo}", path),
                        severity="critical",
                        category="tracked_file",
                        source=f"{target.owner}/{target.repo}/{path}",
                        snippet=path,
                        suggested_fix=f"remove {path} via commit + push",
                        fixer="github_api",
                        fix_payload={"action": "delete_file", "owner": target.owner,
                                     "repo": target.repo, "path": path},
                    )
                )
                break
    return findings
