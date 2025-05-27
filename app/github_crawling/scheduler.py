# app/github_crawling/scheduler.py

from app.github_crawling.github_team_repos_from_urls import get_all_repos_from_team_urls
from app.github_crawling.github_api import fetch_commits, fetch_prs, fetch_readme, fetch_closed_issues, fetch_commit_stats, fetch_contents, fetch_contributors, fetch_workflows
from app.github_crawling.parser import parse_commit_item, parse_pr_item, parse_readme
from app.github_crawling.text_splitter import split_text
from app.github_crawling.embedding import get_embedding
from app.github_crawling.vector_store import store_document, is_id_exists
from app.github_crawling.issue_connect_pr_check import fetch_pr_from_issue
from collections import defaultdict
import hashlib
import chromadb

from dotenv import load_dotenv
load_dotenv()

REPOS = get_all_repos_from_team_urls()
client = chromadb.PersistentClient(path="./chroma_db_e5_base")
collection = client.get_or_create_collection(name="github_docs")

def save_vector_entry(raw: str, doc_id_prefix: str, repo: str, team_id: int, team_number: str):
    chunks = split_text(raw)
    for idx, chunk in enumerate(chunks):
        chunk_id = f"{doc_id_prefix}_chunk{idx}"
        if is_id_exists(chunk_id):
            print(f"⚠️ 이미 저장된 ID: {chunk_id} → 생략")
            continue
        try:
            embedding = get_embedding(chunk)
            store_document(
                text=chunk,
                metadata={
                    "repo": repo,
                    "date": doc_id_prefix.split("_")[-1],
                    "team_id": team_id,
                    "team_number": team_number
                },
                embedding=embedding,
                doc_id=chunk_id
            )
            print(f"📥 저장 완료: {chunk_id}")
        except Exception as e:
            print(f"❌ 저장 실패: {repo} / {chunk_id} / {e}")


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
            doc_id_prefix = f"{repo}_{day}"
            save_vector_entry(combined, doc_id_prefix, repo, team_id, team_number)

        def save_aux(doc_type, raw):
            content_hash = hash_text(raw)
            doc_id_prefix = f"{repo}_{doc_type}_{content_hash}"
            if is_id_exists(doc_id_prefix + "_chunk0"):
                print(f"⚠️ {doc_type} 변경 없음 → 생략")
            else:
                save_vector_entry(raw, doc_id_prefix, repo, team_id, team_number)

        if (content := fetch_readme(repo)):
            save_aux("README", parse_readme(content))

        if (contents := fetch_contents(repo)):
            raw = "\n".join(f"{c['type'].upper()}: {c['path']}" for c in contents)
            save_aux("CONTENTS", raw)

        if (contributors := fetch_contributors(repo)):
            raw = "\n".join(f"{c['login']}: {c['contributions']} commits" for c in contributors)
            save_aux("CONTRIBUTOR", raw)

        if (stats := fetch_commit_stats(repo)):
            raw = "\n".join(f"{s['author']['login']}: {sum(w.get('c', 0) for w in s['weeks'])} commits" for s in stats if "author" in s)
            save_aux("STATS", raw)

        for wf in fetch_workflows(repo):
            wf_id = wf.get("id") or hash_text(wf["name"] + wf.get("created_at", ""))
            doc_id_prefix = f"{repo}_WORKFLOW_{wf_id}"
            if is_id_exists(doc_id_prefix + "_chunk0"):
                print(f"⚠️ Workflow {wf['name']} 이미 있음 → 생략")
            else:
                raw = f"Workflow: {wf['name']} / Status: {wf['status']} / Conclusion: {wf['conclusion']}"
                save_vector_entry(raw, doc_id_prefix, repo, team_id, team_number)

if __name__ == "__main__":
    main()



# PYTHONPATH=. python app/github_crawling/scheduler.py