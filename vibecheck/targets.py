"""Parse target strings into typed Target objects."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Union


class TargetParseError(ValueError):
    """Raised when a target string cannot be parsed."""


@dataclass
class LocalRepoTarget:
    path: Path


@dataclass
class RemoteRepoTarget:
    owner: str
    repo: str


@dataclass
class ProfileTarget:
    user: str


@dataclass
class IssueTarget:
    owner: str
    repo: str
    number: int


@dataclass
class PullRequestTarget:
    owner: str
    repo: str
    number: int


@dataclass
class GistTarget:
    owner: str
    gist_id: str


Target = Union[
    LocalRepoTarget,
    RemoteRepoTarget,
    ProfileTarget,
    IssueTarget,
    PullRequestTarget,
    GistTarget,
]


_GH_REPO = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)/?$")
_GH_PROFILE = re.compile(r"^https://github\.com/([^/]+?)/?$")
_GH_ISSUE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/issues/(\d+)/?$")
_GH_PR = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")
_GH_GIST = re.compile(r"^https://gist\.github\.com/([^/]+)/([a-f0-9]+)/?$")
_HANDLE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}[A-Za-z0-9])?$")


def parse_target(raw: str) -> Target:
    raw = raw.strip()
    if not raw:
        raise TargetParseError("empty target")

    # Local path first (covers "." and existing directories)
    p = Path(raw)
    if p.exists() and p.is_dir():
        return LocalRepoTarget(path=p.resolve())

    if m := _GH_ISSUE.match(raw):
        return IssueTarget(owner=m.group(1), repo=m.group(2), number=int(m.group(3)))
    if m := _GH_PR.match(raw):
        return PullRequestTarget(owner=m.group(1), repo=m.group(2), number=int(m.group(3)))
    if m := _GH_GIST.match(raw):
        return GistTarget(owner=m.group(1), gist_id=m.group(2))
    if m := _GH_REPO.match(raw):
        return RemoteRepoTarget(owner=m.group(1), repo=m.group(2))
    if m := _GH_PROFILE.match(raw):
        return ProfileTarget(user=m.group(1))
    if _HANDLE.match(raw):
        return ProfileTarget(user=raw)

    raise TargetParseError(f"could not parse target: {raw!r}")


def parse_targets_file(path: Path) -> list[Target]:
    targets: list[Target] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        targets.append(parse_target(s))
    return targets
