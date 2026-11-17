"""GitHub Profile Card

Type a GitHub username and see their profile, followers, repos and
most-used languages, using live data from the GitHub REST API.
"""

import re
import sys
from collections import Counter

import requests


API_URL = "https://api.github.com"
TIMEOUT = 10  # seconds; never wait forever for the API
USERNAME_RE = re.compile(r"^[A-Za-z0-9-]{1,39}$")  # letters, numbers, hyphens


class GitHubError(Exception):
    """Raised with a friendly message when GitHub data cannot be fetched."""


def github_get(path, params=None):
    """GET one GitHub API path and return the parsed JSON."""
    headers = {"Accept": "application/vnd.github+json"}
    try:
        resp = requests.get(
            API_URL + path, params=params, headers=headers, timeout=TIMEOUT
        )
    except requests.RequestException as error:
        raise GitHubError(
            "Could not reach GitHub. Check your internet connection and try again."
        ) from error

    if resp.status_code == 404:
        raise GitHubError("User not found. Check the spelling of the username.")
    if resp.status_code in (403, 429):
        raise GitHubError(
            "GitHub rate limit reached (60 requests per hour without a token). "
            "Wait a while and try again."
        )
    if not resp.ok:
        raise GitHubError(
            f"GitHub returned an unexpected error (status {resp.status_code})."
        )
    try:
        return resp.json()
    except ValueError as error:
        raise GitHubError("GitHub sent a response we could not read.") from error


def get_user(username):
    """Fetch the public profile of a GitHub user."""
    return github_get(f"/users/{username}")


def get_repos(username):
    """Fetch up to 100 of the user's public repos (most recently updated first)."""
    return github_get(
        f"/users/{username}/repos", params={"per_page": 100, "sort": "updated"}
    )


def own_repos(repos):
    """Keep only the user's own repos (forks are mostly someone else's work)."""
    return [repo for repo in repos if not repo.get("fork")]


def top_languages(repos, limit=5):
    """Return the most common languages as (language, repo_count) pairs."""
    counts = Counter(
        repo["language"] for repo in own_repos(repos) if repo.get("language")
    )
    return counts.most_common(limit)


def total_stars(repos):
    """Add up the stars on the user's own repos."""
    return sum(repo.get("stargazers_count", 0) for repo in own_repos(repos))


def format_card(user, repos):
    """Build the text of the profile card."""
    line = "=" * 50
    name = user.get("name") or user["login"]
    languages = top_languages(repos)
    known = sum(1 for repo in own_repos(repos) if repo.get("language"))

    card = [
        line,
        f"  {name} (@{user['login']})",
        f"  {user['html_url']}",
        line,
        f"  Bio          : {user.get('bio') or '-'}",
        f"  Location     : {user.get('location') or '-'}",
        f"  Member since : {user['created_at'][:10]}",
        f"  Public repos : {user['public_repos']:,}",
        f"  Followers    : {user['followers']:,}",
        f"  Following    : {user['following']:,}",
        f"  Stars earned : {total_stars(repos):,}",
        "-" * 50,
        "  Most-used languages",
    ]
    if languages:
        for language, count in languages:
            bar = "#" * max(1, round(20 * count / known))
            noun = "repo" if count == 1 else "repos"
            share = f"{count / known:.0%}"
            card.append(f"    {language:<12} {bar:<20} {count} {noun} ({share})")
    else:
        card.append("    No language data found.")
    card.append(line)
    card.append("  Based on up to 100 recent public repos (forks excluded).")
    return "\n".join(card)


def main():
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input("GitHub username: ")
    username = username.strip()

    if not USERNAME_RE.fullmatch(username):
        print("Error: a GitHub username has only letters, numbers and hyphens.")
        return 1

    try:
        user = get_user(username)
        repos = get_repos(username)
    except GitHubError as error:
        print(f"Error: {error}")
        return 1

    print(format_card(user, repos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
