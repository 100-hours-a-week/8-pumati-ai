# app/github_crawling/github_api.py

import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import subprocess
import base64
from dateutil import parser as date_parser

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_latest_wiki_modified_date(clone_path: str) -> str:
    """
    Git log를 통해 최근 wiki 커밋 시간(=최근 수정일)을 가져옵니다.
    반환값: ISO 날짜 문자열 (예: "2025-06-24")
    """
    try:
        result = subprocess.run(
            ["git", "-C", clone_path, "log", "-1", "--format=%cd", "--date=iso"],
            capture_output=True, text=True, check=True
        )
        latest_date = result.stdout.strip()
        parsed_date = date_parser.parse(latest_date)
        return parsed_date.date().isoformat()
    except Exception as e:
        print(f"❌ wiki 수정일 파싱 실패: {e}")
        return datetime.utcnow().date().isoformat()

def fetch_commits(repo: str, per_page=100, max_pages=10):
    all_commits = []
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/repos/{repo}/commits?per_page={per_page}&page={page}"
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            break
        items = res.json()
        if not items:
            break
        for item in items:
            all_commits.append({
                "type": "commit",
                "repo": repo,
                "message": item["commit"]["message"],
                "date": item["commit"]["committer"]["date"]
            })
    return all_commits

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
    if res.status_code != 200:
        return None

    content = base64.b64decode(res.json()["content"]).decode("utf-8")

    # 수정일자 가져오기
    last_modified_str = res.headers.get("Last-Modified")
    if last_modified_str:
        last_modified = datetime.strptime(last_modified_str, "%a, %d %b %Y %H:%M:%S %Z")
        date_str = last_modified.date().isoformat()
    else:
        date_str = datetime.utcnow().date().isoformat()

    return {
        "content": content,
        "date": date_str
    }

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

    modified_date = get_latest_wiki_modified_date(clone_path)

    pages = {}
    for fname in os.listdir(clone_path):
        if fname.endswith(".md"):
            with open(os.path.join(clone_path, fname), encoding="utf-8") as f:
                pages[fname] = {
                    "content": f.read(),
                    "date": modified_date
                }

    return pages