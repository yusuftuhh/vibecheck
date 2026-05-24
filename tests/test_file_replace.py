"""Tests for local file replace/delete fixer."""
import subprocess
from pathlib import Path

from vibecheck.findings import Finding
from vibecheck.fixers.file_replace import apply_file_fix


def test_apply_file_fix_replaces_text(tmp_repo: Path):
    f = tmp_repo / "doc.md"
    f.write_text("Hello — world")
    finding = Finding(
        id="x", severity="info", category="em_dash",
        source=str(f), snippet="—", suggested_fix="replace",
        fixer="file_replace",
        fix_payload={"source": str(f), "find": "—", "replace": "-"},
    )
    apply_file_fix(finding)
    assert f.read_text() == "Hello - world"


def test_apply_file_fix_deletes_file(tmp_repo: Path):
    f = tmp_repo / "CLAUDE.md"
    f.write_text("# notes")
    subprocess.run(["git", "-C", str(tmp_repo), "add", "CLAUDE.md"], check=True)
    finding = Finding(
        id="x", severity="critical", category="tracked_file",
        source=str(f), snippet="CLAUDE.md", suggested_fix="delete",
        fixer="file_replace",
        fix_payload={"action": "delete", "path": "CLAUDE.md", "repo": str(tmp_repo)},
    )
    apply_file_fix(finding)
    assert not f.exists()
