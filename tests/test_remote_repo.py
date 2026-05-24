"""Tests for remote repo scanning via GitHub API."""
import httpx
import respx

from vibecheck.config import Config
from vibecheck.github_client import GitHubClient
from vibecheck.scanners.remote_repo import scan_remote_repo
from vibecheck.targets import RemoteRepoTarget


@respx.mock
def test_scan_remote_repo_finds_co_author_commit():
    target = RemoteRepoTarget(owner="u", repo="r")
    respx.get("https://api.github.com/repos/u/r/commits", params={"per_page": "100", "page": "1"}).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "sha": "abc1234567890",
                    "commit": {
                        "author": {"email": "x@example.com"},
                        "message": "feat: foo\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
                    },
                }
            ],
        )
    )
    respx.get("https://api.github.com/repos/u/r/branches", params={"per_page": "100", "page": "1"}).mock(
        return_value=httpx.Response(200, json=[{"name": "main"}])
    )
    respx.get("https://api.github.com/repos/u/r/git/trees/HEAD", params={"recursive": "1"}).mock(
        return_value=httpx.Response(200, json={"tree": []})
    )

    client = GitHubClient(token="t")
    findings = scan_remote_repo(target, client, Config())
    assert any(f.category == "commit_message" and "Co-Authored-By" in f.snippet for f in findings)


@respx.mock
def test_scan_remote_repo_finds_helper_file():
    target = RemoteRepoTarget(owner="u", repo="r")
    respx.get("https://api.github.com/repos/u/r/commits", params={"per_page": "100", "page": "1"}).mock(
        return_value=httpx.Response(200, json=[])
    )
    respx.get("https://api.github.com/repos/u/r/branches", params={"per_page": "100", "page": "1"}).mock(
        return_value=httpx.Response(200, json=[{"name": "main"}])
    )
    respx.get("https://api.github.com/repos/u/r/git/trees/HEAD", params={"recursive": "1"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "tree": [
                    {"path": "src/main.py", "type": "blob"},
                    {"path": "CLAUDE.md", "type": "blob"},
                ]
            },
        )
    )

    client = GitHubClient(token="t")
    findings = scan_remote_repo(target, client, Config())
    assert any(f.category == "tracked_file" and "CLAUDE.md" in f.snippet for f in findings)


@respx.mock
def test_scan_remote_repo_finds_ai_branch():
    target = RemoteRepoTarget(owner="u", repo="r")
    respx.get("https://api.github.com/repos/u/r/commits", params={"per_page": "100", "page": "1"}).mock(
        return_value=httpx.Response(200, json=[])
    )
    respx.get("https://api.github.com/repos/u/r/branches", params={"per_page": "100", "page": "1"}).mock(
        return_value=httpx.Response(200, json=[{"name": "main"}, {"name": "claude/wip"}])
    )
    respx.get("https://api.github.com/repos/u/r/git/trees/HEAD", params={"recursive": "1"}).mock(
        return_value=httpx.Response(200, json={"tree": []})
    )

    client = GitHubClient(token="t")
    findings = scan_remote_repo(target, client, Config())
    assert any(f.category == "branch_name" and "claude/wip" in f.snippet for f in findings)
