# app/github_crawling/vector_store.py

import chromadb
from datetime import datetime
from app.github_crawling.text_splitter import split_text
from app.github_crawling.embedding import get_embedding
from app.github_crawling.github_api import (
    fetch_commits, fetch_prs, fetch_readme, fetch_closed_issues
)

from dotenv import load_dotenv
load_dotenv()

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
    if "home" in filename or "vision" in filename:
        weight += 0.5
    metadata["weight"] = weight

    

    # metadata["weight"] = default_weights.get(doc_type, 1.0)

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