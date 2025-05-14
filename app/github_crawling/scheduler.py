# app/github_crawling/scheduler.py

from github_team_repos import get_all_repos_from_team_urls
from github_api import fetch_commits, fetch_prs, fetch_readme
from parser import parse_commit_item, parse_pr_item, parse_readme
from text_splitter import split_text
from embedding import get_embedding
from vector_store import store_document

REPOS = get_all_repos_from_team_urls()

# def main():
#     for repo in REPOS:
#         print(f"\n🚀 Start crawling: {repo}")
        
#         commits = fetch_commits(repo)
#         print(f"📝 커밋 수: {len(commits)}")
        
#         prs = fetch_prs(repo)
#         print(f"🔁 PR 수: {len(prs)}")
        
#         readme = fetch_readme(repo)
#         print(f"📘 README 있음?: {'있음' if readme else '없음'}")

def main():
    for repo in REPOS:
        # 커밋
        for item in fetch_commits(repo):
            parsed = parse_commit_item(item)
            print(f"[📄 커밋 크롤링 결과] repo={repo} / date={item['date']} / len={len(parsed)}")
            for chunk in split_text(parsed):
                store_document(chunk, {"repo": repo, "date": item["date"]}, get_embedding(chunk))
        
        # PR
        for item in fetch_prs(repo):
            parsed = parse_pr_item(item)
            print(f"[📄 PR 크롤링 결과] repo={repo} / date={item['date']} / len={len(parsed)}")
            for chunk in split_text(parsed):
                store_document(chunk, {"repo": repo, "date": item["date"]}, get_embedding(chunk))

        # README
        content = fetch_readme(repo)
        if content:
            parsed = parse_readme(content)
            print(f"[📄 README 크롤링 결과] repo={repo} / len={len(parsed)}")
            for chunk in split_text(parsed):
                store_document(chunk, {"repo": repo, "date": "README"}, get_embedding(chunk))

if __name__ == "__main__":
    main()
