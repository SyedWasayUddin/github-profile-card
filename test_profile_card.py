"""Unit tests for profile_card.py. They use fake API responses, so they run
offline and never use up your GitHub rate limit."""

import pytest
import requests

import profile_card as pc

USER = {
    "login": "demo-user",
    "name": "Demo User",
    "html_url": "https://github.com/demo-user",
    "bio": None,
    "location": "Karachi",
    "created_at": "2021-03-14T09:00:00Z",
    "public_repos": 5,
    "followers": 12,
    "following": 5,
}

REPOS = [
    {"language": "Python", "stargazers_count": 5, "fork": False},
    {"language": "Python", "stargazers_count": 2, "fork": False},
    {"language": "C", "stargazers_count": 1, "fork": False},
    {"language": "JavaScript", "stargazers_count": 100, "fork": True},  # fork: ignored
    {"language": None, "stargazers_count": 0, "fork": False},  # no language: ignored
]


class FakeResponse:
    """Just enough of requests.Response for our code."""

    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        if self._data is None:
            raise ValueError("no JSON body")
        return self._data


def fake_api(monkeypatch, status=200):
    """Replace requests.get with a fake that never touches the network."""
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        if status != 200:
            return FakeResponse(status, {})
        return FakeResponse(200, REPOS if url.endswith("/repos") else USER)

    monkeypatch.setattr(pc.requests, "get", fake_get)
    return calls


# ---- data helpers -------------------------------------------------------
def test_top_languages_counts_and_ignores_forks_and_missing():
    assert pc.top_languages(REPOS) == [("Python", 2), ("C", 1)]


def test_top_languages_respects_limit():
    assert pc.top_languages(REPOS, limit=1) == [("Python", 2)]


def test_total_stars_ignores_forks():
    assert pc.total_stars(REPOS) == 8


def test_format_card_shows_key_facts():
    card = pc.format_card(USER, REPOS)
    assert "Demo User (@demo-user)" in card
    assert "Followers    : 12" in card
    assert "Python" in card
    assert "2 repos (67%)" in card


def test_format_card_handles_no_repos():
    assert "No language data found." in pc.format_card(USER, [])


# ---- talking to the API -------------------------------------------------
def test_github_get_sends_a_timeout(monkeypatch):
    calls = fake_api(monkeypatch)
    pc.get_user("demo-user")
    assert calls[0][1]["timeout"] == pc.TIMEOUT


def test_user_not_found(monkeypatch):
    fake_api(monkeypatch, status=404)
    with pytest.raises(pc.GitHubError, match="not found"):
        pc.get_user("nobody")


def test_rate_limit(monkeypatch):
    fake_api(monkeypatch, status=403)
    with pytest.raises(pc.GitHubError, match="rate limit"):
        pc.get_user("demo-user")


def test_server_error(monkeypatch):
    fake_api(monkeypatch, status=500)
    with pytest.raises(pc.GitHubError, match="500"):
        pc.get_user("demo-user")


def test_network_down(monkeypatch):
    def boom(url, **kwargs):
        raise requests.ConnectionError("no internet")

    monkeypatch.setattr(pc.requests, "get", boom)
    with pytest.raises(pc.GitHubError, match="Could not reach GitHub"):
        pc.get_user("demo-user")


# ---- token from the environment ----------------------------------------
def test_token_added_when_set(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "abc123")
    assert pc.build_headers()["Authorization"] == "Bearer abc123"


def test_no_token_no_auth_header(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert "Authorization" not in pc.build_headers()


# ---- the whole program --------------------------------------------------
def test_main_prints_card(monkeypatch, capsys):
    fake_api(monkeypatch)
    monkeypatch.setattr(pc.sys, "argv", ["profile_card.py", "demo-user"])
    assert pc.main() == 0
    assert "Demo User (@demo-user)" in capsys.readouterr().out


@pytest.mark.parametrize("bad_name", ["", "has space", "../etc", "a" * 40])
def test_main_rejects_bad_usernames(monkeypatch, capsys, bad_name):
    fake_api(monkeypatch)
    monkeypatch.setattr(pc.sys, "argv", ["profile_card.py", bad_name])
    monkeypatch.setattr("builtins.input", lambda prompt="": bad_name)
    assert pc.main() == 1
    assert "Error" in capsys.readouterr().out


def test_main_reports_missing_user(monkeypatch, capsys):
    fake_api(monkeypatch, status=404)
    monkeypatch.setattr(pc.sys, "argv", ["profile_card.py", "nobody"])
    assert pc.main() == 1
    assert "User not found" in capsys.readouterr().out
