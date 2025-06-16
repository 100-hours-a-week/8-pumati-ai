# app/github_crawling/github_api.py

import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import subprocess

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

def get_wiki_clone_path(repo: str) -> str:
    """repo 이름 기반으로 고정된 wiki 경로 생성"""
    owner, name = repo.split("/")
    return os.path.join("./cached_wikis", f"{owner}_{name}")

def fetch_wiki_md_files(repo: str) -> dict:
    """
    Wiki 저장소를 git clone해서 md 파일을 불러옴.
    이미 있으면 clone하지 않음.
    """
    clone_path = get_wiki_clone_path(repo)

    if not os.path.exists(clone_path):
        print(f"📥 Cloning wiki for {repo}...")
        os.makedirs("./cached_wikis", exist_ok=True)
        wiki_git_url = f"https://{GITHUB_TOKEN}@github.com/{repo}.wiki.git"
        subprocess.run(["git", "clone", wiki_git_url, clone_path], check=True)
        # clone 이후 폴더가 생성되었는지 확인
        if os.path.exists(clone_path):
            print(f"📁 Wiki cloned and saved to: {clone_path}")
        else:
            print(f"❌ Cloning seems to have failed: {clone_path} not found")
    else:
        print(f"✅ Wiki already cloned for {repo} → 생략")

    pages = {}
    for fname in os.listdir(clone_path):
        if fname.endswith(".md"):
            with open(os.path.join(clone_path, fname), encoding="utf-8") as f:
                pages[fname] = f.read()
    return pages