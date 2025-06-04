# app/github_crawling/github_team_repos_from_urls.py

import requests
import os
import re
from dotenv import load_dotenv

# 환경변수에서 GitHub 토큰 로드
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

ORG_NAME = "100-hours-a-week"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# 주어진 팀 URL 리스트
TEAM_URLS = [
    "https://github.com/orgs/100-hours-a-week/teams/8",
    # "https://github.com/orgs/100-hours-a-week/teams/20",
    "https://github.com/orgs/100-hours-a-week/teams/7-1"
    # "https://github.com/orgs/100-hours-a-week/teams/13-cafeboo"
]

# 예시: slug → id 매핑 (실제 환경에서는 DB나 config로 관리할 것)
TEAM_META = {
    "8": 1,
    "7-1": 2,
    "13-cafeboo": 3,
    # 필요에 따라 추가
}

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

    # 확인용
    print("\n✅ 전체 REPOS 리스트")
    print("REPOS = [")
    for r in all_repos:
        print(f'    "{r[0]}",')
    print("]")

    return all_repos

if __name__ == "__main__":
    get_all_repos_from_team_urls()
