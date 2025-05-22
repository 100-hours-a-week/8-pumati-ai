# app/github_crawling/check_vector.py
from chromadb import PersistentClient

client = PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="github_docs")

results = collection.get(include=["documents", "metadatas", "embeddings"], limit=100)

print("\n📦 총 벡터 수:", collection.count())

print("\n🧾 저장된 벡터 샘플:")
for i in range(min(len(results["documents"]), 10)):
    doc_id = results["metadatas"][i].get("repo", "(unknown)") + "_" + results["metadatas"][i].get("date", "?")
    print(f"\n📝 [{i+1}] ID: {doc_id}")
    print(f"📄 Document: {results['documents'][i][:200]}...")
    print(f"🗂️ Metadata: {results['metadatas'][i]}")

# 메타데이터 통계 요약
print("\n📊 팀 ID 및 팀 넘버 통계:")
from collections import defaultdict

team_count = defaultdict(int)
for meta in results["metadatas"]:
    key = f"{meta.get('team_number', 'unknown')} (ProjectID: {meta.get('project_id', '-')})"
    team_count[key] += 1

for team, count in sorted(team_count.items(), key=lambda x: x[0]):
    print(f"🔹 {team}: {count}개")

# 저장된 레포 요약
repo_names = set()
for m in results["metadatas"]:
    if m and "repo" in m:
        repo_names.add(m["repo"])

print("\n📁 저장된 repo 목록:")
for r in sorted(repo_names):
    print(f"📌 {r}")
