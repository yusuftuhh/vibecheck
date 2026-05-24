"""Tests for the httpx-based GitHub client."""
import os

import httpx
import pytest
import respx

from vibecheck.github_client import GitHubClient, GitHubError, RateLimitError


def test_token_from_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    client = GitHubClient()
    assert client.token == "secret-token"


def test_no_token_unauthenticated(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("vibecheck.github_client._gh_cli_token", lambda: None)
    client = GitHubClient()
    assert client.token is None


@respx.mock
def test_get_returns_json():
    respx.get("https://api.github.com/users/u").mock(
        return_value=httpx.Response(200, json={"login": "u", "id": 1})
    )
    client = GitHubClient(token="t")
    data = client.get("/users/u")
    assert data["login"] == "u"


@respx.mock
def test_404_returns_none():
    respx.get("https://api.github.com/users/missing").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    client = GitHubClient(token="t")
    assert client.get("/users/missing") is None


@respx.mock
def test_rate_limit_raises():
    respx.get("https://api.github.com/users/u").mock(
        return_value=httpx.Response(
            403,
            json={"message": "API rate limit exceeded"},
            headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1700000000"},
        )
    )
    client = GitHubClient(token="t")
    with pytest.raises(RateLimitError):
        client.get("/users/u")


@respx.mock
def test_paginated_aggregates_all_pages():
    respx.get("https://api.github.com/users/u/repos", params={"per_page": "100", "page": "1"}).mock(
        return_value=httpx.Response(
            200,
            json=[{"name": "r1"}, {"name": "r2"}],
            headers={"link": '<https://api.github.com/users/u/repos?page=2>; rel="next"'},
        )
    )
    respx.get("https://api.github.com/users/u/repos", params={"per_page": "100", "page": "2"}).mock(
        return_value=httpx.Response(200, json=[{"name": "r3"}])
    )
    client = GitHubClient(token="t")
    items = client.paginated("/users/u/repos")
    assert [it["name"] for it in items] == ["r1", "r2", "r3"]


@respx.mock
def test_server_error_raises_github_error():
    respx.get("https://api.github.com/users/u").mock(return_value=httpx.Response(500))
    client = GitHubClient(token="t")
    with pytest.raises(GitHubError):
        client.get("/users/u")
