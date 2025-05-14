# app/github_crawling/check_vector.py
from vector_store import show_vector_summary

# show_vector_summary()

import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="github_docs")

print("📦 총 벡터 수:", collection.count())

docs = collection.peek(5)
for i in range(len(docs["ids"])):
    print(f"\n📝 [{i+1}] ID: {docs['ids'][i]}")
    print(f"📄 Document: {docs['documents'][i][:150]}...")
    print(f"🗂️ Metadata: {docs['metadatas'][i]}")
    print(f"🔢 Vector Length: {len(docs['embeddings'][i])}")

