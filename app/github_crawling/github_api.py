# app/github_crawling/github_api.py

import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
SINCE = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"

def fetch_commits(repo: str):
    url = f"https://api.github.com/repos/{repo}/commits"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200: return []
    return [
        {
            "type": "commit",
            "repo": repo,
            "message": item["commit"]["message"],
            "date": item["commit"]["committer"]["date"]
        }
        for item in res.json()
    ]

def fetch_prs(repo: str):
    url = f"https://api.github.com/repos/{repo}/pulls?state=closed&sort=updated&direction=desc"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200: return []
    return [
        {
            "type": "pr",
            "repo": repo,
            "title": pr["title"],
            "body": pr["body"],
            "date": pr["closed_at"]
        }
        for pr in res.json() if pr["closed_at"]
    ]

def fetch_issues(repo: str):
    url = f"https://api.github.com/repos/{repo}/issues?state=closed"
    res = requests.get(url, headers=HEADERS)
    return [
        {
            "type": "issue",
            "repo": repo,
            "title": issue["title"],
            "body": issue["body"],
            "date": issue["closed_at"]
        }
        for issue in res.json() if "pull_request" not in issue
    ]

def fetch_readme(repo: str):
    url = f"https://api.github.com/repos/{repo}/readme"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200: return None
    import base64
    return base64.b64decode(res.json()["content"]).decode("utf-8")


# Branches / Tags
# Commit diff + file stats
# GitHub Actions
# Issues, Pulls
# GitHub Tree API
# Contributors