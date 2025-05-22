# app/github_crawling/scheduler.py

from app.github_crawling.github_team_repos_from_urls import get_all_repos_from_team_urls
from github_api import fetch_commits, fetch_prs, fetch_readme, fetch_closed_issues, fetch_commit_stats, fetch_contents, fetch_contributors, fetch_workflows
from parser import parse_commit_item, parse_pr_item, parse_readme
from text_splitter import split_text
from embedding import get_embedding
from vector_store import store_document, is_id_exists
from llm_summary import generate_summary
from issue_connect_pr_check import fetch_pr_from_issue
from collections import defaultdict
import hashlib
import chromadb

REPOS = get_all_repos_from_team_urls()
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="github_docs")

def save_vector_entry(raw: str, doc_id: str, repo: str, team_id: int, team_number: str):
    if is_id_exists(doc_id):
        print(f"⚠️ 이미 저장된 ID: {doc_id} → 요약 및 저장 생략")
        return

    try:
        print(f"🌀 요약 시작: {repo} / {doc_id}")
        summary = generate_summary(raw)  # ← LLM 추론
    except Exception as e:
        print(f"❌ 요약 실패: {repo} / {doc_id} / {e}")
        return

    try:
        embedding = get_embedding(summary)
        store_document(summary, {
            "repo": repo,
            "date": doc_id.split("_")[-1],  # doc_id에서 날짜 추출
            "raw": raw,
            "team_id": team_id,
            "team_number": team_number
        }, embedding, doc_id=doc_id)
        print(f"📥 저장 완료: {doc_id}")
    except Exception as e:
        print(f"❌ 저장 실패: {repo} / {doc_id} / {e}")

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def main():
    for repo_entry in REPOS:
        repo, team_id, team_number = repo_entry

        print(f"\n🚀 Start crawling: {repo} (Team ID: {team_id}, Number: {team_number})")

        entries_by_day = defaultdict(list)

        for item in fetch_commits(repo):
            day = item["date"][:10]
            entries_by_day[day].append(parse_commit_item(item))

        for item in fetch_prs(repo):
            day = item["date"][:10]
            entries_by_day[day].append(parse_pr_item(item))

        for issue in fetch_closed_issues(repo):
            day = issue["closed_at"][:10]
            raw = f"Issue: {issue['title']}\n\n{issue['body']}"
            pr_info = fetch_pr_from_issue(repo, issue["number"])
            if pr_info:
                raw += f"\n\n🔗 Related PR: {pr_info['pr_url']}"
            entries_by_day[day].append(raw)

        for day, raw_list in entries_by_day.items():
            combined = "\n\n".join(f"- {entry}" for entry in raw_list)
            doc_id = f"{repo}_{day}"
            save_vector_entry(combined, doc_id, repo, team_id, team_number)

        content = fetch_readme(repo)
        if content:
            raw = parse_readme(content)
            content_hash = hash_text(raw)
            doc_id = f"{repo}_README_{content_hash}"
            existing = collection.get(ids=[doc_id], include=["documents"])
            if existing["ids"]:
                print(f"⚠️ README 내용 변경 없음 → 요약 생략")
            else:
                save_vector_entry(raw, doc_id, repo, team_id, team_number)

        contents = fetch_contents(repo)
        if contents:
            summary_raw = "\n".join(f"{c['type'].upper()}: {c['path']}" for c in contents)
            content_hash = hash_text(summary_raw)
            doc_id = f"{repo}_CONTENTS_{content_hash}"
            existing = collection.get(ids=[doc_id], include=["documents"])
            if existing["ids"]:
                print(f"⚠️ CONTENTS 변경 없음 → 요약 생략")
            else:
                save_vector_entry(summary_raw, doc_id, repo, team_id, team_number)

        contributors = fetch_contributors(repo)
        if contributors:
            summary_raw = "\n".join(f"{c['login']}: {c['contributions']} commits" for c in contributors)
            content_hash = hash_text(summary_raw)
            doc_id = f"{repo}_CONTRIBUTOR_{content_hash}"
            existing = collection.get(ids=[doc_id], include=["documents"])
            if existing["ids"]:
                print(f"⚠️ CONTRIBUTORS 변경 없음 → 요약 생략")
            else:
                save_vector_entry(summary_raw, doc_id, repo, team_id, team_number)

        stats = fetch_commit_stats(repo)
        if stats:
            summary_raw = "\n".join(
                f"{s['author']['login']}: {sum(w.get('c', 0) for w in s['weeks'])} commits"
                for s in stats if "author" in s
            )
            content_hash = hash_text(summary_raw)
            doc_id = f"{repo}_STATS_{content_hash}"
            existing = collection.get(ids=[doc_id], include=["documents"])
            if existing["ids"]:
                print(f"⚠️ STATS 변경 없음 → 요약 생략")
            else:
                save_vector_entry(summary_raw, doc_id, repo, team_id, team_number)

        workflows = fetch_workflows(repo)
        for wf in workflows:
            wf_id = wf.get("id") or hash_text(wf["name"] + wf.get("created_at", ""))
            doc_id = f"{repo}_WORKFLOW_{wf_id}"
            existing = collection.get(ids=[doc_id], include=["documents"])
            if existing["ids"]:
                print(f"⚠️ Workflow {wf['name']} 이미 있음 → 생략")
            else:
                raw = f"Workflow: {wf['name']} / Status: {wf['status']} / Conclusion: {wf['conclusion']}"
                save_vector_entry(raw, doc_id, repo, team_id, team_number)

if __name__ == "__main__":
    main()



# PYTHONPATH=. python app/github_crawling/scheduler.py