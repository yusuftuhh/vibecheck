"""Tests for the CLI entry point."""
from pathlib import Path
from unittest.mock import patch, MagicMock

from vibecheck.cli import main
from vibecheck.findings import Finding


def test_cli_no_args_scans_cwd(tmp_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_repo)
    with patch("vibecheck.cli.scan_local_repo", return_value=[]) as scan:
        exit_code = main([])
    assert exit_code == 0
    scan.assert_called_once()


def test_cli_scan_remote_repo(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_TOKEN", "tkn")
    with patch("vibecheck.cli.scan_remote_repo", return_value=[]) as scan:
        exit_code = main(["scan", "https://github.com/u/r"])
    assert exit_code == 0
    scan.assert_called_once()


def test_cli_json_output(tmp_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_repo)
    finding = Finding("a", "critical", "c", "s", "snip", "fix", "fixer", {})
    with patch("vibecheck.cli.scan_local_repo", return_value=[finding]):
        main(["--json"])
    out = capsys.readouterr().out
    assert '"id": "a"' in out
    assert '"summary"' in out


def test_cli_fix_items_calls_fixers(tmp_repo: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_repo)
    finding = Finding("abc12345", "info", "em_dash", str(tmp_repo / "x.md"), "—", "fix",
                      "file_replace",
                      {"source": str(tmp_repo / "x.md"), "find": "—", "replace": "-"})
    (tmp_repo / "x.md").write_text("hello — world")
    with patch("vibecheck.cli.scan_local_repo", return_value=[finding]):
        exit_code = main(["fix", "--items", "abc12345"])
    assert exit_code == 0
    assert (tmp_repo / "x.md").read_text() == "hello - world"
