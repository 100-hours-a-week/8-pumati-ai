# app/github_crawling/github_team_repos_from_urls.py

import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ORG_NAME = os.getenv("ORG_NAME")
TEAM_LIST_API_URL = os.getenv("TEAM_LIST_API_URL")
USE_BACKEND_API = os.getenv("USE_BACKEND_API", "true").lower() == "true"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def fetch_team_meta():
    if USE_BACKEND_API:
        try:
            res = requests.get(TEAM_LIST_API_URL, timeout=10)
            res.raise_for_status()
            result = res.json()
            team_urls = []
            team_meta = {}
            for item in result["data"]:
                url = item["githubUrl"]
                project_id = item["projectId"]
                slug = url.split("/")[-1]
                team_urls.append(url)
                team_meta[slug] = project_id
            return team_urls, team_meta
        except Exception as e:
            print(f"❌ [API 실패] 팀 목록을 불러오는 데 실패했습니다, api/projects/github-urls실패, 백엔드 서버 켜졌는지 확인 필요: {e}")
            return [], {}
    else:
        # 수동 fallback
        team_urls = [
            "https://github.com/orgs/100-hours-a-week/teams/8",
            # "https://github.com/orgs/100-hours-a-week/teams/7-1",
            # "https://github.com/orgs/100-hours-a-week/teams/20",
            # "https://github.com/orgs/100-hours-a-week/teams/13-cafeboo",

        ]
        team_meta = {
            "8": 1,
            # "7-1": 2
        }
        return team_urls, team_meta

def extract_team_slugs_from_urls(urls):
    slugs = []
    for url in urls:
        match = re.search(r'/teams/([^/]+)$', url)
        if match:
            slugs.append(match.group(1))
    return slugs

def get_team_repos(org, team_slug):
    url = f"https://api.github.com/orgs/{org}/teams/{team_slug}/repos"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)  # timeout 추가
        if res.status_code == 404:
            print(f"❌ [Team: {team_slug}] Not found or no access.")
            return []
        res.raise_for_status()
        return res.json()
    except requests.exceptions.Timeout:
        print(f"⏱️ [Team: {team_slug}] 요청 시간이 초과되었습니다.")
        return []
    except requests.exceptions.RequestException as e:
        print(f"⚠️ [Team: {team_slug}] 요청 중 오류 발생: {e}")
        return []


def get_all_repos_from_team_urls():
    TEAM_URLS, TEAM_META = fetch_team_meta()
    team_slugs = extract_team_slugs_from_urls(TEAM_URLS)
    all_repos = []
    for slug in team_slugs:
        try:
            repos = get_team_repos(ORG_NAME, slug)
            team_id = TEAM_META.get(slug, 0)
            for repo in repos:
                all_repos.append((repo["full_name"], team_id, slug)) 
        except Exception as e:
            print(f"⚠️ 팀 {slug} 에러: {e}")
    print("\n✅ 전체 REPOS 리스트")
    print("REPOS = [")
    for r in all_repos:
        print(f'    "{r[0]}",')
    print("]")
    return all_repos

if __name__ == "__main__":
    get_all_repos_from_team_urls()
