# app/github_crawling/issue_connect_pr_check.py

import requests
from app.github_crawling.github_api import HEADERS

def fetch_pr_from_issue(repo: str, issue_number: int):
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/timeline"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        return None

    for event in res.json():
        if event.get("event") == "connected":
            pr = event.get("source", {}).get("issue", {}).get("pull_request")
            if pr:
                pr_num = event["source"]["issue"]["number"]
                return {
                    "pr_number": pr_num,
                    "pr_url": f"https://github.com/{repo}/pull/{pr_num}"
                }

    return None
