# app/github_crawling/scheduler.py

from app.github_crawling.github_team_repos_from_urls import get_all_repos_from_team_urls
from app.github_crawling.github_api import fetch_commits, fetch_prs, fetch_readme, fetch_closed_issues
from app.github_crawling.vector_store import store_document, is_id_exists, show_vector_summary
from collections import defaultdict
from app.github_crawling.github_api import fetch_wiki_md_files
from app.model_inference.rag_chat_runner import embedding_model
from dotenv import load_dotenv
load_dotenv()

import json
from datetime import date, timedelta
from pathlib import Path
from datetime import datetime
from dateutil.parser import parse
from app.github_crawling.vector_store import delete_document_if_exists
from app.model_inference.loaders.gemini_langchain_llm import summarize_chain

PART_LIST = ["ai", "be", "cloud", "fe", "wiki"]
def classify_part_from_repo(repo_name: str) -> str:
    lowered = repo_name.lower()
    for part in PART_LIST:
        if f"-{part}" in lowered:
            return part.upper()
    return "others"

LAST_RUN_FILE = Path("last_run_date.json")
FORCE_RUN = False # 일주일 단위가 아닌 바로 실행

def is_weekly_run_due() -> bool:
    if not LAST_RUN_FILE.exists():
        return True
    with open(LAST_RUN_FILE, "r") as f:
        last_run_str = json.load(f).get("last_run", "")
        try:
            last_run = date.fromisoformat(last_run_str)
            return (date.today() - last_run) >= timedelta(days=7)
        except:
            return True

def update_last_run_date():
    with open(LAST_RUN_FILE, "w") as f:
        json.dump({"last_run": date.today().isoformat()}, f)

def clean_iso_date(iso_str: str) -> str:
    return iso_str.replace("Z", "+00:00")

def generate_week_ranges(start_date: datetime, end_date: datetime):
    week_ranges = []
    start = start_date
    end = end_date
    while start < end:
        week_start = start
        week_end = min(start + timedelta(days=6), end)
        week_ranges.append((week_start.date().isoformat(), week_end.date().isoformat()))
        start += timedelta(days=7)
    return week_ranges


def group_data_by_week(data, week_ranges):
    weekly_data = defaultdict(list)
    for item in data:
        item_date = datetime.fromisoformat(clean_iso_date(item["date"])).date()
        for week_start, week_end in week_ranges:
            if week_start <= item_date.isoformat() <= week_end:
                weekly_data[(week_start, week_end)].append(item)
                break
    return weekly_data


def summarize_weekly_data(weekly_data_dict, repo, project_id, team_id):
    part = classify_part_from_repo(repo)

    for (week_start, week_end), items in weekly_data_dict.items():
        if not items:
            continue

        doc_id = f"summary-{team_id}-{part}-{week_end[5:7]}-{week_end[8:10]}"
        if is_id_exists(doc_id):
            print(f"✅ 이미 저장된 문서: {doc_id} → 생략")
            continue

        #요약 직접 실행
        raw_text = "\n".join(item.get("message", item.get("title", "")) for item in items)
        print(f"🔍 Gemini 요약 중... Team: {team_id}, Part: {part}")
        summary = summarize_chain.invoke({"input": raw_text})

        #메타데이터 구성
        metadata = {
            "repo": repo,
            "date": week_end,
            "project_id": project_id,
            "team_id": team_id,
            "type": "summary",
            "part": part
        }

        #직접 store_document 호출 (가중치 자동 적용됨)
        print(f"📅 요약 결과 저장 중... ID: {doc_id}")
        store_document(summary, metadata, embedding_model, doc_id)

def summarize_wiki_pages(repo, project_id, team_id):
    pages = fetch_wiki_md_files(repo)
    if not pages:
        print("❌ Wiki pages가 없습니다.")
        return

    part = "WIKI"
    wiki_date = list(pages.values())[0]["date"]  # 최신 커밋일

    sorted_page_items = sorted(pages.items())  # 페이지 이름 기준 정렬
    chunk_size = 10
    chunk_count = (len(sorted_page_items) + chunk_size - 1) // chunk_size

    for i in range(chunk_count):
        chunk = sorted_page_items[i * chunk_size: (i + 1) * chunk_size]

        combined_text = ""
        for fname, page in chunk:
            combined_text += f"# {fname}\n{page['content']}\n\n"

        chunk_id = i + 1
        doc_id = f"summary-{team_id}-{part}-{wiki_date[5:7]}-{wiki_date[8:10]}-chunk{chunk_id:02}"

        # 이미 있다면 삭제 후 다시 생성
        if is_id_exists(doc_id):
            print(f"🗑️ 기존 요약 문서 삭제: {doc_id}")
            delete_document_if_exists(doc_id)

        metadata = {
            "repo": repo,
            "date": wiki_date,
            "project_id": project_id,
            "team_id": team_id,
            "type": "summary",
            "part": part,
            "chunk": chunk_id
        }

        print(f"🧾 wiki 문서 요약 저장: {doc_id} (페이지 {i * chunk_size + 1}~{(i + 1) * chunk_size})")
        summary = summarize_chain.invoke({"input": combined_text.strip()})
        store_document(summary, metadata, embedding_model, doc_id)

def main():
    should_run = FORCE_RUN or is_weekly_run_due()

    if not should_run:
        has_existing_data = LAST_RUN_FILE.exists()
        if has_existing_data:
            print("➡️ 이번 주는 이미 실행됨. 생략합니다.")
            return

    # run 조건을 통과한 경우에만 실행
    update_last_run_date()
    print("🚀 일주일에 한 번 실행되는 요약 파이프라인 시작")
    
    REPOS = get_all_repos_from_team_urls()

    for repo_entry in REPOS:
        repo, project_id, team_id = repo_entry
        print(f"\n🚀 Start crawling: {repo} (Team ID: {project_id}, Number: {team_id})")

        if repo.endswith("-wiki"): # wiki는 별도 처리
            summarize_wiki_pages(repo, project_id, team_id)
            continue  # 아래 크롤링 로직 건너뜀

        all_items = []
        readme_data = fetch_readme(repo)
        if readme_data:
            all_items.append({
                "type": "readme",
                "repo": repo,
                "title": "README",
                "body": readme_data["content"],
                "date": readme_data["date"]
            })

        for item in fetch_commits(repo):
            all_items.append(item)
        for item in fetch_prs(repo):
            all_items.append(item)
        for issue in fetch_closed_issues(repo):
            all_items.append({
                "type": "issue",
                "repo": repo,
                "title": issue["title"],
                "body": issue["body"],
                "date": issue["closed_at"]
            })

        print(f"📅 크롤링된 전체 항목 수: {len(all_items)}")
        for item in all_items:
            print(" -", item.get("date", "날짜 없음"), item.get("type", "unknown"))

        if not all_items:
            continue

        # 날짜 파싱 및 유효 항목 필터링
        valid_dates = []
        for item in all_items:
            date_str = item.get("date")
            try:
                parsed_date = parse(date_str)
                valid_dates.append(parsed_date)
                item["parsed_date"] = parsed_date  # 나중에 그룹핑에 활용 가능
            except Exception:
                print("⚠️ 날짜 파싱 실패:", date_str)

        if not valid_dates:
            print("❌ 날짜 정보가 없어 요약을 건너뜁니다.")
            continue

        date_min = min(valid_dates)
        date_max = max(valid_dates)

        print("📆 date_min:", date_min)
        print("📆 date_max:", date_max)

        week_ranges = generate_week_ranges(date_min, date_max)
        print("📅 생성된 주차 리스트:")
        for start, end in week_ranges:
            print(f" - {start} ~ {end}")

        grouped = group_data_by_week(all_items, week_ranges)
        for week, items in grouped.items():
            print(f"🗓️ {week[0]} ~ {week[1]}: {len(items)}개 항목")

        summarize_weekly_data(grouped, repo, project_id, team_id)

if __name__ == "__main__":
    main()
    show_vector_summary()

# PYTHONPATH=. python app/github_crawling/scheduler.py