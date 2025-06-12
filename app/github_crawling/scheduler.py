# app/github_crawling/scheduler.py

from app.github_crawling.github_team_repos_from_urls import get_all_repos_from_team_urls
from app.github_crawling.github_api import fetch_commits, fetch_prs, fetch_readme, fetch_closed_issues, fetch_commit_stats, fetch_contents, fetch_contributors
from app.github_crawling.parser import parse_commit_item, parse_pr_item, parse_readme
from app.github_crawling.text_splitter import split_text
from app.github_crawling.embedding import get_embedding
from app.github_crawling.vector_store import store_document, is_id_exists, show_vector_summary
from app.github_crawling.issue_connect_pr_check import fetch_pr_from_issue
from collections import defaultdict
import hashlib
from app.github_crawling.github_api import fetch_wiki_md_files

from dotenv import load_dotenv
load_dotenv()

def save_vector_entry(raw: str, doc_id_prefix: str, repo: str, project_id: int, team_id: int):
    chunks = split_text(raw)
    for idx, chunk in enumerate(chunks):
        chunk_id = f"{doc_id_prefix}_chunk{idx}"
        # 중복 방지: UUID 기준으로 동일 ID 생성하여 체크
        from uuid import uuid5, NAMESPACE_DNS
        uuid_id = str(uuid5(NAMESPACE_DNS, chunk_id))
        if is_id_exists(uuid_id):
            print(f"➡️ UUID 기준 이미 저장된 ID: {chunk_id} → 생략")
            continue
        try:
            embedding = get_embedding(chunk)
            store_document(
                text=chunk,
                metadata={
                    "repo": repo,
                    "date": doc_id_prefix.split("_")[-1],
                    "project_id": project_id,
                    "team_id": team_id
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
    REPOS = get_all_repos_from_team_urls()

    for repo_entry in REPOS:
        repo, project_id, team_id = repo_entry
        print(f"\n🚀 Start crawling: {repo} (Team ID: {project_id}, Number: {team_id})")

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
            save_vector_entry(combined, doc_id_prefix, repo, project_id, team_id)

        def save_aux(doc_type, raw):
            content_hash = hash_text(raw)
            doc_id_prefix = f"{repo}_{doc_type}_{content_hash}"
            if is_id_exists(doc_id_prefix + "_chunk0"):
                print(f"➡️ {doc_type} 변경 없음 → 생략")
            else:
                save_vector_entry(raw, doc_id_prefix, repo, project_id, team_id)

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

        try:
            wiki_pages = fetch_wiki_md_files(repo)
            for filename, content in wiki_pages.items():
                doc_id_prefix = f"{repo}_wiki_{filename}"
                save_vector_entry(
                    raw=content,
                    doc_id_prefix=doc_id_prefix,
                    repo=repo,
                    project_id=project_id,
                    team_id=team_id
                )
        except Exception as e:
            print(f"❌ Wiki 저장 실패: {repo} / {e}")

if __name__ == "__main__":
    main()
    show_vector_summary()

# PYTHONPATH=. python app/github_crawling/scheduler.py