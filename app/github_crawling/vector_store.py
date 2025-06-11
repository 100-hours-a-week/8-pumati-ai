# app/github_crawling/vector_store.py

import os
import chromadb
from datetime import datetime
from app.github_crawling.text_splitter import split_text
from app.github_crawling.embedding import get_embedding
from app.github_crawling.github_api import (
    fetch_commits, fetch_prs, fetch_readme, fetch_closed_issues
)

from dotenv import load_dotenv
load_dotenv()

USE_REMOTE_CHROMA = os.getenv("USE_REMOTE_CHROMA", "false").lower() == "true"

if USE_REMOTE_CHROMA:
    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", "8000"))
    client = chromadb.HttpClient(host=host, port=port)
else:
    client = chromadb.PersistentClient(path="./chroma_db_weight")

collection = client.get_or_create_collection(name="github_docs")

def is_id_exists(doc_id: str) -> bool:
    existing = collection.get(ids=[doc_id], include=["documents"])
    return bool(existing["ids"])


def store_document(text: str, metadata: dict, embedding: list, doc_id: str):
    """
    청크 단위 텍스트를 임베딩과 함께 저장합니다.
    metadata에 weight를 자동 부여하여 저장합니다.
    """
    # type으로 weight 추론
    doc_type = metadata.get("type", "other").lower()
    filename = metadata.get("filename", "").lower()

    default_weights = {
        "commit": 0.1,
        "pr": 1.2,
        "issue": 1.0,
        "readme": 1.0,
        "contents": 0.8,
        "contributor": 0.5,
        "stats": 0.5,
        "wiki":0.7,
    }
    weight = default_weights.get(doc_type, 1.0)
    if "Home" in filename or "Vision" in filename:
        weight += 1.0
    if "프로젝트" in text or "서비스" in text:
        weight += 1.0
    metadata["weight"] = weight

    print("✅  저장 직전 metadata:", metadata)
    print("✅ project_id 타입:", type(metadata.get("project_id")))

    collection.add(
        documents=[text],
        metadatas=[metadata],
        embeddings=[embedding],
        ids=[doc_id]
    )



def show_vector_summary():
    client = chromadb.PersistentClient(path="./chroma_db_weight")
    collection = client.get_collection(name="github_docs")
    
    print("📦 총 벡터 수:", collection.count())
    
    docs = collection.peek(3)
    print("🔍 일부 문서 미리보기:")
    for doc in docs:
        print("-", doc[:120], "...")