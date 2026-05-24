"""Tests for issue/PR comments scanning."""
import httpx
import respx

from vibecheck.config import Config
from vibecheck.github_client import GitHubClient
from vibecheck.scanners.comments import scan_user_comments


@respx.mock
def test_scan_user_comments_via_search():
    respx.get(
        "https://api.github.com/search/issues",
        params={"q": "commenter:u", "per_page": "100", "page": "1"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "html_url": "https://github.com/u/r/issues/1",
                        "comments_url": "https://api.github.com/repos/u/r/issues/1/comments",
                    }
                ]
            },
        )
    )
    respx.get("https://api.github.com/repos/u/r/issues/1/comments").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 100, "user": {"login": "u"}, "body": "I'd be happy to help — sure"},
                {"id": 101, "user": {"login": "other"}, "body": "nope"},
            ],
        )
    )

    client = GitHubClient(token="t")
    findings = scan_user_comments("u", client, Config())
    assert any("I'd be happy to" in f.snippet for f in findings)
    assert all(f.fix_payload.get("comment_id") == 100 for f in findings)
