"""Tests for report rendering."""
import json
from io import StringIO

from vibecheck.findings import Finding
from vibecheck.report import render_human, render_json


def test_render_json_serializes_all_fields():
    findings = [
        Finding("a", "critical", "commit_message", "src1", "snip1", "fix1", "fixer1",
                {"k": "v"}),
        Finding("b", "info", "em_dash", "src2", "snip2", "fix2", "fixer2", {}),
    ]
    out = render_json(findings, scan_targets=["github.com/u"])
    data = json.loads(out)
    assert data["version"]
    assert data["summary"]["critical"] == 1
    assert data["summary"]["info"] == 1
    assert len(data["findings"]) == 2
    assert data["findings"][0]["fix_payload"] == {"k": "v"}


def test_render_human_groups_by_severity(capsys):
    findings = [
        Finding("a", "critical", "commit_message", "src", "snip", "fix", "fixer", {}),
        Finding("b", "warning", "branch_name", "src", "snip", "fix", "fixer", {}),
        Finding("c", "info", "em_dash", "src", "snip", "fix", "fixer", {}),
    ]
    render_human(findings, scan_targets=["x"])
    captured = capsys.readouterr().out
    assert "critical" in captured.lower()
    assert "warning" in captured.lower()
    assert "info" in captured.lower()
    assert "src" in captured
    assert "a" in captured  # id shown


def test_render_human_empty(capsys):
    render_human([], scan_targets=["clean.example.com"])
    out = capsys.readouterr().out
    assert "no findings" in out.lower() or "clean" in out.lower()
