# app/github_crawling/vector_store.py

import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="github_docs")

def store_document(text: str, metadata: dict, embedding: list):
    collection.add(
        documents=[text], # 실제 요약 텍스트
        metadatas=[metadata], # 커밋/PR/README의 출처 정보
        embeddings=[embedding], # 임베딩 벡터 (list of float)
        ids=[f"{metadata['repo']}_{metadata['date']}"] # 고유 ID (예: 8-pumati-ai_2025-05-01T08:34)
    )

def show_vector_summary():
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="github_docs")
    
    print("📦 총 벡터 수:", collection.count())
    
    docs = collection.peek(3)
    print("🔍 일부 문서 미리보기:")
    for doc in docs:
        print("-", doc[:120], "...")

# 배포된 db용
# import chromadb
# import os
# from dotenv import load_dotenv

# # 환경변수 로드
# load_dotenv()  # 기본 .env 경로에서 읽어옴

# CHROMA_HOST = os.getenv("localhost")
# CHROMA_PORT = int(os.getenv("8000")

# # Docker로 분리된 Chroma 서버에 연결
# client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
# collection = client.get_or_create_collection(name="github_docs")

# def store_document(text: str, metadata: dict, embedding: list):
#     collection.add(
#         documents=[text],
#         metadatas=[metadata],
#         embeddings=[embedding],
#         ids=[f"{metadata['repo']}_{metadata['date']}"]
#     )

# def show_vector_summary():
#     print("📦 총 벡터 수:", collection.count())

#     docs = collection.peek(3)
#     print("🔍 일부 문서 미리보기:")
#     for i in range(len(docs["ids"])):
#         print(f"\n📝 [{i+1}] ID: {docs['ids'][i]}")
#         print(f"📄 Document: {docs['documents'][i][:120]}...")
#         print(f"🗂️ Metadata: {docs['metadatas'][i]}")

