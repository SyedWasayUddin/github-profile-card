"""GitHub Profile Card

Type a GitHub username and see their profile, followers, repos and
most-used languages, using live data from the GitHub REST API.
"""

import requests


API_URL = "https://api.github.com"
TIMEOUT = 10  # seconds; never wait forever for the API


def get_user(username):
    """Fetch the public profile of a GitHub user."""
    resp = requests.get(f"{API_URL}/users/{username}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def main():
    username = input("GitHub username: ").strip()
    user = get_user(username)
    print(f"{user['name'] or user['login']} has {user['followers']} followers")


if __name__ == "__main__":
    main()
