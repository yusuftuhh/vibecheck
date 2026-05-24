"""Tests for git-history fixer."""
import os
import subprocess
from pathlib import Path

from vibecheck.findings import Finding
from vibecheck.fixers.git_history import apply_git_history_fix


def _commit(repo: Path, msg: str):
    (repo / "f.txt").write_text(msg)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", msg], check=True)


def test_strip_line_from_commit_message(tmp_repo: Path):
    _commit(tmp_repo, "feat: thing\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    finding = Finding(
        id="x", severity="critical", category="commit_message",
        source="commit ...", snippet="Co-Authored-By: Claude",
        suggested_fix="strip", fixer="git_history",
        fix_payload={"strip_line_match": "Co-Authored-By: Claude <noreply@anthropic.com>",
                     "repo": str(tmp_repo)},
    )
    apply_git_history_fix(finding)
    log = subprocess.run(["git", "-C", str(tmp_repo), "log", "--format=%B"],
                         capture_output=True, text=True, check=True).stdout
    assert "Co-Authored-By" not in log


def test_delete_branch(tmp_repo: Path):
    _commit(tmp_repo, "initial")
    subprocess.run(["git", "-C", str(tmp_repo), "branch", "claude/wip"], check=True)
    finding = Finding(
        id="x", severity="warning", category="branch_name",
        source=str(tmp_repo), snippet="claude/wip",
        suggested_fix="delete", fixer="git_history",
        fix_payload={"action": "delete_branch", "branch": "claude/wip", "repo": str(tmp_repo)},
    )
    apply_git_history_fix(finding)
    branches = subprocess.run(["git", "-C", str(tmp_repo), "branch"],
                              capture_output=True, text=True, check=True).stdout
    assert "claude/wip" not in branches
