# app/github_crawling/parser.py

def parse_commit_item(item):
    return f"{item['date']}에 {item['repo']}에서 커밋됨: {item['message']}"

def parse_pr_item(item):
    return f"{item['date']}에 PR 병합됨: {item['title']}"

def parse_readme(content):
    lines = content.splitlines()
    return "\n".join(lines[:20])  # 상단 요약만
