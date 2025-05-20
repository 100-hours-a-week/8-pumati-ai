# app/github_crawling/check_vector.py
from vector_store import show_vector_summary

# show_vector_summary()

import chromadb

# client = chromadb.PersistentClient(path="./chroma_db")
# collection = client.get_collection(name="github_docs")

# print("📦 총 벡터 수:", collection.count())

# docs = collection.peek(5)
# for i in range(len(docs["ids"])):
#     print(f"\n📝 [{i+1}] ID: {docs['ids'][i]}")
#     print(f"📄 Document: {docs['documents'][i][:150]}...")
#     print(f"🗂️ Metadata: {docs['metadatas'][i]}")
#     print(f"🔢 Vector Length: {len(docs['embeddings'][i])}")

# client = chromadb.PersistentClient(path="./chroma_db")
# collection = client.get_or_create_collection(name="team_documents")

# results = collection.get(include=["documents", "metadatas"], limit=100)

# repo_names = set()
# for m in results["metadatas"]:
#     if m and "repo" in m:
#         repo_names.add(m["repo"])

# print("\n🧾 저장된 repo 메타데이터 종류:")
# for r in sorted(repo_names):
#     print(f"🔹 {r}")

from chromadb import PersistentClient

client = PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="github_docs")

results = collection.get(include=["metadatas"], limit=100)

team_ids = set()
for meta in results["metadatas"]:
    if meta and "repo" in meta:
        team_ids.add(meta["repo"])

print("✅ 현재 ChromaDB에 저장된 repo 값들:")
for repo in sorted(team_ids):
    print(f"🔹 {repo}")