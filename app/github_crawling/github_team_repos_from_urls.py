# app/github_crawling/github_team_repos_from_urls.py

import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ORG_NAME = os.getenv("ORG_NAME")
TEAM_LIST_API_URL = os.getenv("TEAM_LIST_API_URL")
USE_BACKEND_API_RAW = os.getenv("USE_BACKEND_API")
USE_BACKEND_API = USE_BACKEND_API_RAW and USE_BACKEND_API_RAW.lower() == "true"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# USE_BACKEND_API=False # 테스트용

def fetch_team_meta():
    print(f"🐛 USE_BACKEND_API 값: {USE_BACKEND_API}")
    if USE_BACKEND_API:
        print("🌐 백엔드 API를 통해 팀 메타데이터를 가져옵니다.")
        print(f"🔗 요청 URL: {TEAM_LIST_API_URL}")
        try:
            res = requests.get(TEAM_LIST_API_URL, timeout=10)
            print(f"📥 응답 상태 코드: {res.status_code}")
            res.raise_for_status()

            result = res.json()
            print(f"📦 API 응답 내용: {result}")

            # 'data' 필드 유효성 검사 추가
            if "data" not in result:
                print(f"❌ API 응답에 'data' 필드가 없습니다. result: {result}")
                return [], {}

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
        # 수동 fallback 테스트용
        team_urls = [
            "https://github.com/orgs/100-hours-a-week/teams/8",
            # "https://github.com/orgs/100-hours-a-week/teams/1",
            # "https://github.com/orgs/100-hours-a-week/teams/7-1",
            # "https://github.com/orgs/100-hours-a-week/teams/20",
            # "https://github.com/orgs/100-hours-a-week/teams/13-cafeboo",

        ]
        team_meta = {
            "8": 6,
            # "1": 9
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
