"""Tests for GitHub API fixer (comments, bio, gists, README)."""
import base64
import httpx
import respx

from vibecheck.findings import Finding
from vibecheck.fixers.github_api import apply_github_api_fix
from vibecheck.github_client import GitHubClient


@respx.mock
def test_update_comment_replaces_substring():
    respx.get("https://api.github.com/repos/u/r/issues/comments/100").mock(
        return_value=httpx.Response(200, json={"id": 100, "body": "I'd be happy to help"})
    )
    route = respx.patch("https://api.github.com/repos/u/r/issues/comments/100").mock(
        return_value=httpx.Response(200, json={"id": 100, "body": "happy to help"})
    )

    finding = Finding(
        id="x", severity="info", category="comment",
        source="x", snippet="I'd be happy to", suggested_fix="strip",
        fixer="github_api",
        fix_payload={
            "action": "update_comment",
            "comment_url": "https://api.github.com/repos/u/r/issues/comments/100",
            "comment_id": 100,
            "find": "I'd be happy to ",
            "replace": "",
        },
    )
    client = GitHubClient(token="t")
    apply_github_api_fix(finding, client)
    assert route.called


@respx.mock
def test_update_bio():
    respx.patch("https://api.github.com/user").mock(
        return_value=httpx.Response(200, json={"login": "u", "bio": "clean"})
    )
    finding = Finding(
        id="x", severity="info", category="bio", source="x", snippet="\U0001f916",
        suggested_fix="strip", fixer="github_api",
        fix_payload={"action": "update_bio", "user": "u", "find": "\U0001f916", "replace": ""},
    )
    client = GitHubClient(token="t")
    apply_github_api_fix(finding, client)


@respx.mock
def test_update_profile_readme():
    encoded = base64.b64encode(b"old content with em-dash \xe2\x80\x94 here").decode()
    respx.get("https://api.github.com/repos/u/u/contents/README.md").mock(
        return_value=httpx.Response(200, json={"content": encoded, "sha": "abc"})
    )
    route = respx.put("https://api.github.com/repos/u/u/contents/README.md").mock(
        return_value=httpx.Response(200, json={"commit": {"sha": "new"}})
    )
    finding = Finding(
        id="x", severity="info", category="profile_readme", source="x", snippet="—",
        suggested_fix="strip", fixer="github_api",
        fix_payload={"action": "update_profile_readme", "user": "u", "sha": "abc",
                     "find": "—", "replace": "-"},
    )
    client = GitHubClient(token="t")
    apply_github_api_fix(finding, client)
    assert route.called
