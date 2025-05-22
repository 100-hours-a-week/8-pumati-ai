# app/github_crawling/vector_store_no_llm.py

import chromadb

client = chromadb.PersistentClient(path="./chroma_db_no_llm")
collection = client.get_or_create_collection(name="github_docs")

def is_id_exists(doc_id: str) -> bool:
    existing = collection.get(ids=[doc_id], include=["documents"])
    return bool(existing["ids"])

def store_document(text: str, metadata: dict, embedding: list, doc_id: str):
    collection.add(
        documents=[text],
        metadatas=[metadata],
        embeddings=[embedding],
        ids=[doc_id]
    )
