"""Scan a local git repo for AI-attribution traces."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from vibecheck.config import Config
from vibecheck.findings import Finding, generate_id


def scan_local_repo(repo_path: Path, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_scan_commits(repo_path, config))
    findings.extend(_scan_tracked_files(repo_path, config))
    findings.extend(_scan_branches(repo_path, config))
    return findings


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout


def _scan_commits(repo: Path, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    raw = _git(repo, "log", "--all", "--format=%H%x1f%ae%x1f%B%x1e")
    for entry in raw.split("\x1e"):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("\x1f")
        if len(parts) < 3:
            continue
        sha, email, body = parts[0], parts[1], parts[2]

        for pat in config.bot_email_patterns:
            if pat in email:
                findings.append(
                    Finding(
                        id=generate_id("commit_author", sha, email),
                        severity="critical",
                        category="commit_author",
                        source=f"commit {sha[:8]}",
                        snippet=email,
                        suggested_fix="rewrite commit author via git filter-branch",
                        fixer="git_history",
                        fix_payload={"sha": sha, "field": "author", "value": email},
                    )
                )
                break

        for line in body.splitlines():
            if re.match(r"(?i)co-authored-by:.*(claude|anthropic|copilot|gpt|openai)", line):
                findings.append(
                    Finding(
                        id=generate_id("commit_message", sha, line),
                        severity="critical",
                        category="commit_message",
                        source=f"commit {sha[:8]}",
                        snippet=line.strip(),
                        suggested_fix="strip line from commit message",
                        fixer="git_history",
                        fix_payload={"sha": sha, "strip_line_match": line.strip()},
                    )
                )
            elif "\U0001f916" in line or "Generated with Claude" in line or "Generated with ChatGPT" in line:
                findings.append(
                    Finding(
                        id=generate_id("commit_message", sha, line),
                        severity="warning",
                        category="commit_message",
                        source=f"commit {sha[:8]}",
                        snippet=line.strip(),
                        suggested_fix="strip line from commit message",
                        fixer="git_history",
                        fix_payload={"sha": sha, "strip_line_match": line.strip()},
                    )
                )
    return findings


def _scan_tracked_files(repo: Path, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    tracked = _git(repo, "ls-files").splitlines()
    for path in tracked:
        for pattern in config.file_paths:
            if pattern.endswith("/"):
                if path.startswith(pattern):
                    _add_file_finding(findings, repo, path, pattern)
                    break
            elif "*" in pattern:
                import fnmatch
                if fnmatch.fnmatch(path, pattern):
                    _add_file_finding(findings, repo, path, pattern)
                    break
            elif path == pattern:
                _add_file_finding(findings, repo, path, pattern)
                break
    return findings


def _add_file_finding(findings: list, repo: Path, path: str, pattern: str) -> None:
    findings.append(
        Finding(
            id=generate_id("tracked_file", str(repo), path),
            severity="critical",
            category="tracked_file",
            source=f"{repo}/{path}",
            snippet=path,
            suggested_fix=f"untrack {path} and add to .gitignore",
            fixer="file_replace",
            fix_payload={"action": "delete", "path": path, "repo": str(repo)},
        )
    )


def _scan_branches(repo: Path, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    branches = _git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/").splitlines()
    for branch in branches:
        for pattern in config.branch_patterns:
            if re.match(pattern, branch):
                findings.append(
                    Finding(
                        id=generate_id("branch_name", str(repo), branch),
                        severity="warning",
                        category="branch_name",
                        source=f"{repo} branch {branch}",
                        snippet=branch,
                        suggested_fix=f"delete or rename branch {branch}",
                        fixer="git_history",
                        fix_payload={"action": "delete_branch", "branch": branch, "repo": str(repo)},
                    )
                )
                break
    return findings
