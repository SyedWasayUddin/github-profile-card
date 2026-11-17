# GitHub Profile Card

A small Python command-line tool that turns any GitHub username into a
text "profile card": name, bio, followers, repos, stars and the languages
they use most. All data is fetched **live** from the
[GitHub REST API](https://docs.github.com/en/rest) with the `requests` library.

Built as the Module 1 take-home project of the AI Engineering bootcamp.

## Features

- Fetches a user's public profile and up to 100 of their latest public repos
- Counts the most-used languages (forks are excluded, since they are not the user's own work)
- Adds up stars earned and prints a bar chart of language usage
- Friendly messages instead of crashes: unknown user, GitHub rate limit, no internet, bad input
- Every request has a timeout and its status code is checked
- Optional `GITHUB_TOKEN` (kept in a `.env` file, never committed) to lift the 60 requests/hour limit
- Unit tests that run offline using fake API responses

## Requirements

- Python 3.9 or newer
- An internet connection (no API key needed)

## Installation

```bash
git clone https://github.com/SyedWasayUddin/github-profile-card.git
cd github-profile-card

python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash
# .venv\Scripts\activate           # Windows Command Prompt
# source .venv/bin/activate        # macOS / Linux
.\.venv\Scripts\Activate.ps1       # Windows Powershell

pip install -r requirements.txt
```

## Usage

Pass a username as an argument:

```bash
python profile_card.py octocat
```

or run it without one and type the username when asked:

```bash
python profile_card.py
GitHub username: octocat
```

## Sample output


```text
==================================================
  Syed Wasay Uddin (@SyedWasayUddin)
  https://github.com/SyedWasayUddin
==================================================
  Bio          : -
  Location     : -
  Member since : 2021-11-29
  Public repos : 6
  Followers    : 0
  Following    : 0
  Stars earned : 0
--------------------------------------------------
  Most-used languages
    Python       #####                1 repo (25%)
    PowerShell   #####                1 repo (25%)
    TypeScript   #####                1 repo (25%)
    HTML         #####                1 repo (25%)
==================================================
  Based on up to 100 recent public repos (forks excluded).
```

Errors are reported in one friendly line, for example:

```text
Error: a GitHub username has only letters, numbers and hyphens.
Error: GitHub rate limit reached (60 requests per hour without a token). Wait a while, or add a GITHUB_TOKEN to your .env file.
```

## Optional: use a GitHub token

GitHub allows 60 unauthenticated requests per hour per network. On a shared
network (a lab, a hostel) that can run out quickly. To raise the limit to 5,000:

1. Create a token on GitHub: *Settings > Developer settings > Personal access tokens*. No special permissions are needed for public data.
2. Copy `.env.example` to `.env` and paste the token after `GITHUB_TOKEN=`.

`.env` is listed in `.gitignore`, so your token is never pushed to GitHub.

## Running the tests

```bash
python -m pytest
```

The tests replace `requests.get` with a fake, so they work offline and do not
use up your rate limit.

## How it works

| Step | API call |
| --- | --- |
| Profile (name, bio, followers) | `GET https://api.github.com/users/{username}` |
| Repos (languages, stars) | `GET https://api.github.com/users/{username}/repos?per_page=100&sort=updated` |

## Project files

```text
profile_card.py        the program
test_profile_card.py   pytest unit tests
requirements.txt       Python packages to install
.env.example           template for the optional token
.gitignore             keeps .venv/, .env and __pycache__/ out of Git
```

## Limitations

- Languages and stars are based on the 100 most recently updated public repos.
- GitHub reports one main language per repo, so this is a repo count, not lines of code.
