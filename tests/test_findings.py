"""Tests for the Finding dataclass."""
from vibecheck.findings import Finding, generate_id, group_by_severity


def test_finding_construction():
    f = Finding(
        id="abc12345",
        severity="critical",
        category="commit_message",
        source="github.com/u/r commit a1b2c3d",
        snippet="Co-Authored-By: Claude",
        suggested_fix="strip line from message",
        fixer="git_history",
        fix_payload={"sha": "a1b2c3d", "pattern": "Co-Authored-By: Claude"},
    )
    assert f.id == "abc12345"
    assert f.severity == "critical"


def test_generate_id_is_stable():
    a = generate_id("commit_message", "github.com/u/r commit a1b2c3d", "Co-Authored-By: Claude")
    b = generate_id("commit_message", "github.com/u/r commit a1b2c3d", "Co-Authored-By: Claude")
    assert a == b
    assert len(a) == 8


def test_generate_id_differs_per_input():
    a = generate_id("commit_message", "source1", "snippet1")
    b = generate_id("commit_message", "source2", "snippet1")
    assert a != b


def test_group_by_severity():
    findings = [
        Finding("a", "critical", "cat", "src", "snip", "fix", "fixer", {}),
        Finding("b", "warning", "cat", "src", "snip", "fix", "fixer", {}),
        Finding("c", "critical", "cat", "src", "snip", "fix", "fixer", {}),
        Finding("d", "info", "cat", "src", "snip", "fix", "fixer", {}),
    ]
    grouped = group_by_severity(findings)
    assert len(grouped["critical"]) == 2
    assert len(grouped["warning"]) == 1
    assert len(grouped["info"]) == 1
