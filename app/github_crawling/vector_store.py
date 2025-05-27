# app/github_crawling/vector_store.py

import chromadb
from datetime import datetime
from app.github_crawling.text_splitter import split_text
from app.github_crawling.embedding import get_embedding

from dotenv import load_dotenv
load_dotenv()

client = chromadb.PersistentClient(path="./chroma_db_e5_base")
collection = client.get_or_create_collection(name="github_docs")

def is_id_exists(doc_id: str) -> bool:
    existing = collection.get(ids=[doc_id], include=["documents"])
    return bool(existing["ids"])


def store_document(text: str, metadata: dict, embedding: list, doc_id: str):
    """
    청크 단위 텍스트를 임베딩과 함께 저장합니다.
    """
    collection.add(
        documents=[text],
        metadatas=[metadata],
        embeddings=[embedding],
        ids=[doc_id]
    )



def show_vector_summary():
    client = chromadb.PersistentClient(path="./chroma_db_e5_base")
    collection = client.get_collection(name="github_docs")
    
    print("📦 총 벡터 수:", collection.count())
    
    docs = collection.peek(3)
    print("🔍 일부 문서 미리보기:")
    for doc in docs:
        print("-", doc[:120], "...")