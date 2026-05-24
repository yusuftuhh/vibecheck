"""Apply git history rewrites and branch deletions."""
from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from vibecheck.findings import Finding


def apply_git_history_fix(finding: Finding) -> None:
    payload = finding.fix_payload
    action = payload.get("action")
    repo = Path(payload.get("repo", "."))

    if action == "delete_branch":
        subprocess.run(["git", "-C", str(repo), "branch", "-D", payload["branch"]],
                       check=True, capture_output=True)
        return

    pattern = payload.get("strip_line_match")
    if pattern:
        escaped = shlex.quote(pattern)
        msg_filter = f"grep -vF {escaped}"
        env = {**os.environ, "FILTER_BRANCH_SQUELCH_WARNING": "1"}
        subprocess.run(
            ["git", "-C", str(repo), "filter-branch", "-f", "--msg-filter", msg_filter, "HEAD"],
            check=True, capture_output=True, env=env,
        )
        # remove filter-branch backup ref
        subprocess.run(
            ["git", "-C", str(repo), "update-ref", "-d", "refs/original/refs/heads/main"],
            capture_output=True,
        )
        for branch_line in subprocess.run(
            ["git", "-C", str(repo), "for-each-ref", "--format=%(refname)", "refs/original/"],
            capture_output=True, text=True,
        ).stdout.splitlines():
            subprocess.run(["git", "-C", str(repo), "update-ref", "-d", branch_line],
                           capture_output=True)
