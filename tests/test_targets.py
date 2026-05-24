"""Tests for target string parsing."""
from pathlib import Path

import pytest

from vibecheck.targets import (
    GistTarget,
    IssueTarget,
    LocalRepoTarget,
    ProfileTarget,
    PullRequestTarget,
    RemoteRepoTarget,
    TargetParseError,
    parse_target,
    parse_targets_file,
)


def test_parse_local_path(tmp_repo: Path):
    target = parse_target(str(tmp_repo))
    assert isinstance(target, LocalRepoTarget)
    assert target.path == tmp_repo


def test_parse_local_dot(tmp_repo: Path, monkeypatch):
    monkeypatch.chdir(tmp_repo)
    target = parse_target(".")
    assert isinstance(target, LocalRepoTarget)


def test_parse_remote_repo_url():
    target = parse_target("https://github.com/yusuftuhh/foo")
    assert isinstance(target, RemoteRepoTarget)
    assert target.owner == "yusuftuhh"
    assert target.repo == "foo"


def test_parse_remote_repo_with_trailing_slash():
    target = parse_target("https://github.com/yusuftuhh/foo/")
    assert isinstance(target, RemoteRepoTarget)
    assert target.repo == "foo"


def test_parse_user_handle():
    target = parse_target("yusuftuhh")
    assert isinstance(target, ProfileTarget)
    assert target.user == "yusuftuhh"


def test_parse_profile_url():
    target = parse_target("https://github.com/yusuftuhh")
    assert isinstance(target, ProfileTarget)


def test_parse_issue_url():
    target = parse_target("https://github.com/u/r/issues/123")
    assert isinstance(target, IssueTarget)
    assert target.owner == "u"
    assert target.repo == "r"
    assert target.number == 123


def test_parse_pr_url():
    target = parse_target("https://github.com/u/r/pull/456")
    assert isinstance(target, PullRequestTarget)
    assert target.number == 456


def test_parse_gist_url():
    target = parse_target("https://gist.github.com/u/abc123")
    assert isinstance(target, GistTarget)
    assert target.owner == "u"
    assert target.gist_id == "abc123"


def test_parse_invalid_raises():
    with pytest.raises(TargetParseError):
        parse_target("not a url, not a path, not a handle?!")


def test_parse_targets_file(tmp_path: Path, tmp_repo: Path):
    f = tmp_path / "targets.txt"
    f.write_text(
        f"{tmp_repo}\n"
        "https://github.com/u/r\n"
        "yusuftuhh\n"
        "\n"  # blank line ignored
        "# comment ignored\n"
    )
    targets = parse_targets_file(f)
    assert len(targets) == 3
    assert isinstance(targets[0], LocalRepoTarget)
    assert isinstance(targets[1], RemoteRepoTarget)
    assert isinstance(targets[2], ProfileTarget)
