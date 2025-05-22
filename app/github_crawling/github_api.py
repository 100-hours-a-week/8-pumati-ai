# app/github_crawling/github_api.py

import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

SINCE = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"

def fetch_commits(repo: str):
    url = f"https://api.github.com/repos/{repo}/commits?since={SINCE}"
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

def fetch_readme(repo: str):
    url = f"https://api.github.com/repos/{repo}/readme"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200: return None
    import base64
    return base64.b64decode(res.json()["content"]).decode("utf-8")

def fetch_closed_issues(repo: str):
    url = f"https://api.github.com/repos/{repo}/issues?state=closed"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200: return []
    return [
        {
            "type": "issue",
            "repo": repo,
            "title": issue["title"],
            "body": issue["body"],
            "date": issue["closed_at"],
            "number": issue["number"],
            "closed_at": issue.get("closed_at")
        }
        for issue in res.json() if "pull_request" not in issue
    ]

def fetch_contents(repo: str):
    url = f"https://api.github.com/repos/{repo}/contents"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200: return []
    return res.json()

def fetch_contributors(repo: str):
    url = f"https://api.github.com/repos/{repo}/contributors"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200: return []
    return res.json()

def fetch_commit_stats(repo: str):
    url = f"https://api.github.com/repos/{repo}/stats/contributors"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200: return []
    return res.json()

def fetch_workflows(repo: str):
    url = f"https://api.github.com/repos/{repo}/actions/runs"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200: return []
    return [
        {
            "name": run["name"],
            "status": run["status"],
            "conclusion": run["conclusion"],
            "created_at": run["created_at"]
        }
        for run in res.json().get("workflow_runs", [])
    ]