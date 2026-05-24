"""Tests for profile-wide scanning."""
import httpx
import respx

from vibecheck.config import Config
from vibecheck.github_client import GitHubClient
from vibecheck.scanners.profile import scan_profile
from vibecheck.targets import ProfileTarget


@respx.mock
def test_scan_profile_lists_repos_and_gists_and_scans_bio():
    target = ProfileTarget(user="u")
    respx.get("https://api.github.com/users/u").mock(
        return_value=httpx.Response(200, json={"login": "u", "bio": "I'd be happy to help \U0001f916"})
    )
    respx.get("https://api.github.com/users/u/repos", params={"per_page": "100", "page": "1"}).mock(
        return_value=httpx.Response(200, json=[{"full_name": "u/r1"}, {"full_name": "u/r2"}])
    )
    respx.get("https://api.github.com/users/u/gists", params={"per_page": "100", "page": "1"}).mock(
        return_value=httpx.Response(
            200,
            json=[{"id": "abc", "files": {"snippet.py": {"raw_url": "https://gist/raw"}}, "description": ""}],
        )
    )
    respx.get("https://gist/raw").mock(
        return_value=httpx.Response(200, text="# \U0001f916 Generated with Claude\nprint('hi')")
    )
    respx.get("https://api.github.com/repos/u/u/contents/README.md").mock(
        return_value=httpx.Response(404)
    )

    client = GitHubClient(token="t")
    inventory = scan_profile(target, client, Config())
    assert any(f.category == "bio" and "\U0001f916" in f.snippet for f in inventory.findings)
    assert any(f.category == "gist" for f in inventory.findings)
    assert inventory.repo_targets[0].repo == "r1"
    assert inventory.repo_targets[1].repo == "r2"


@respx.mock
def test_scan_profile_with_readme_repo():
    target = ProfileTarget(user="u")
    respx.get("https://api.github.com/users/u").mock(
        return_value=httpx.Response(200, json={"login": "u", "bio": "clean bio"})
    )
    respx.get("https://api.github.com/users/u/repos", params={"per_page": "100", "page": "1"}).mock(
        return_value=httpx.Response(200, json=[])
    )
    respx.get("https://api.github.com/users/u/gists", params={"per_page": "100", "page": "1"}).mock(
        return_value=httpx.Response(200, json=[])
    )
    respx.get("https://api.github.com/repos/u/u/contents/README.md").mock(
        return_value=httpx.Response(
            200,
            json={"content": "IyBIaSAtIEFzIGFuIEFJ", "encoding": "base64", "path": "README.md", "sha": "x"},
        )
    )

    client = GitHubClient(token="t")
    inventory = scan_profile(target, client, Config())
    # Base64 of "# Hi - As an AI" contains "As an AI"
    assert any(f.category == "profile_readme" and "As an AI" in f.snippet for f in inventory.findings)
