"""Apply local file replacements and deletions."""
from __future__ import annotations

import subprocess
from pathlib import Path

from vibecheck.findings import Finding


def apply_file_fix(finding: Finding) -> None:
    payload = finding.fix_payload
    action = payload.get("action")

    if action == "delete":
        repo = Path(payload["repo"])
        path = repo / payload["path"]
        if path.exists():
            subprocess.run(["git", "-C", str(repo), "rm", "-rf", payload["path"]],
                           check=True, capture_output=True)
        return

    src = Path(payload["source"])
    if not src.exists() or not src.is_file():
        return
    content = src.read_text(encoding="utf-8")
    new = content.replace(payload["find"], payload.get("replace", ""))
    src.write_text(new, encoding="utf-8")
