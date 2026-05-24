"""Tests for local-git repo scanning."""
import subprocess
from pathlib import Path

from vibecheck.config import Config
from vibecheck.scanners.local_git import scan_local_repo


def _make_commit(repo: Path, msg: str, author_email: str = "test@example.com"):
    (repo / "f.txt").write_text(f"{msg}\n")
    subprocess.run(["git", "-C", str(repo), "add", "f.txt"], check=True)
    env = {"GIT_AUTHOR_EMAIL": author_email, "GIT_COMMITTER_EMAIL": author_email,
           "GIT_AUTHOR_NAME": "T", "GIT_COMMITTER_NAME": "T"}
    import os
    full_env = {**os.environ, **env}
    subprocess.run(["git", "-C", str(repo), "commit", "-m", msg], check=True, env=full_env)


def test_scan_finds_co_authored_by_claude(tmp_repo: Path):
    _make_commit(tmp_repo, "feat: thing\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    findings = scan_local_repo(tmp_repo, Config())
    assert any(f.category == "commit_message" and "Co-Authored-By" in f.snippet for f in findings)
    assert any(f.severity == "critical" for f in findings)


def test_scan_finds_bot_email_author(tmp_repo: Path):
    _make_commit(tmp_repo, "feat: x", author_email="bot@anthropic.com")
    findings = scan_local_repo(tmp_repo, Config())
    assert any(f.category == "commit_author" and "anthropic.com" in f.snippet for f in findings)


def test_scan_finds_tracked_helper_file(tmp_repo: Path):
    (tmp_repo / "CLAUDE.md").write_text("# Memory\n")
    subprocess.run(["git", "-C", str(tmp_repo), "add", "CLAUDE.md"], check=True)
    subprocess.run(["git", "-C", str(tmp_repo), "commit", "-m", "add memory"], check=True)
    findings = scan_local_repo(tmp_repo, Config())
    assert any(f.category == "tracked_file" and "CLAUDE.md" in f.snippet for f in findings)


def test_scan_finds_ai_branch_name(tmp_repo: Path):
    _make_commit(tmp_repo, "initial")
    subprocess.run(["git", "-C", str(tmp_repo), "branch", "claude/feature"], check=True)
    findings = scan_local_repo(tmp_repo, Config())
    assert any(f.category == "branch_name" and "claude/feature" in f.snippet for f in findings)


def test_scan_clean_repo_returns_empty(tmp_repo: Path):
    _make_commit(tmp_repo, "feat: clean")
    findings = scan_local_repo(tmp_repo, Config())
    assert findings == []
