# app/github_crawling/vector_store.py

import os
from uuid import uuid5, NAMESPACE_DNS
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PayloadSchemaType
from uuid import uuid5, NAMESPACE_DNS
from app.github_crawling.embedding import get_embedding
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

# 기존 ChromaDB 관련 코드 제거 & Qdrant 설정으로 교체
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_TEAM = os.getenv("QDRANT_COLLECTION_TEAM", "github_docs")
QDRANT_COLLECTION_SUMMARY = os.getenv("QDRANT_COLLECTION_SUMMARY", "summary_docs")

class QdrantCollectionManager:
    def __init__(self, collection_type: str):
        self.client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY
        )

        if collection_type == "summary":
            self.collection = QDRANT_COLLECTION_SUMMARY
        elif collection_type == "team":
            self.collection = QDRANT_COLLECTION_TEAM
        else:
            raise ValueError(f"❌ Unknown collection_type: {collection_type}")

        self._ensure_collection()

    def _ensure_collection(self):
        if not self.client.collection_exists(self.collection):
            print(f"✨ '{self.collection}' 컬렉션이 존재하지 않아 새로 생성합니다.")
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
            for field, ftype in [
                ("project_id", PayloadSchemaType.INTEGER),
                ("team_id", PayloadSchemaType.INTEGER),
                ("repo", PayloadSchemaType.KEYWORD),
                ("type", PayloadSchemaType.KEYWORD),
                ("weight", PayloadSchemaType.FLOAT),
                ("date", PayloadSchemaType.TEXT),
            ]:
                self.client.create_payload_index(self.collection, field_name=field, field_schema=ftype)
        else:
            print(f"➡️ '{self.collection}' 컬렉션이 이미 존재합니다.")

    def get_collection_name(self):
        return self.collection

    def get_client(self):
        return self.client

def is_id_exists(doc_id: str, collection_type: str) -> bool:
    manager = QdrantCollectionManager(collection_type)
    uuid_id = str(uuid5(NAMESPACE_DNS, doc_id))
    result = manager.get_client().retrieve(collection_name=manager.get_collection_name(), ids=[uuid_id])
    return len(result) > 0

def store_document(text, metadata, embedding_model, doc_id, collection_type: str):
    manager = QdrantCollectionManager(collection_type)
    client = manager.get_client()
    collection = manager.get_collection_name()

    doc_type = metadata.get("type", "other").lower()
    part = metadata.get("part", "").lower()
    filename = metadata.get("filename", "").lower()

    default_weights = {
        "commit": 0.9,
        "pr": 1.7,
        "issue": 1.5,
        "readme": 1.3,
        "wiki": 1.7,
        "ai": 1.0,
        "be": 1.0,
        "fe": 1.0,
        "cloud": 1.0,
        "release_note": 3.0,
        "summary": 1.0
    }

    weight = default_weights.get(part, default_weights.get(doc_type, 1.0))

    if "home" in filename or "vision" in filename:
        weight += 1.0
    if "프로젝트" in text or "서비스" in text:
        weight += 1.0
    if "기능" in text:
        weight += 1.0
    metadata["weight"] = weight

    print("✅  저장 직전 metadata:", metadata)

    uuid_id = str(uuid5(NAMESPACE_DNS, doc_id))
    embedding = get_embedding(text)

    client.upsert(
        collection_name=collection,
        points=[{
            "id": uuid_id,
            "vector": embedding,
            "payload": {
                "document": text,
                **metadata
            }
        }]
    )

def show_vector_summary(collection_type: str = "team"):
    manager = QdrantCollectionManager(collection_type)
    client = manager.get_client()
    collection = manager.get_collection_name()

    count = client.count(collection_name=collection).count
    print("📦 총 벡터 수:", count)

    results = client.scroll(
        collection_name=collection,
        limit=3,
        with_payload=True
    )
    print("🔍 일부 문서 미리보기:")
    for point in results[0]:
        doc = point.payload.get("document", "")
        print("-", doc[:120] if isinstance(doc, str) else str(doc), "...")

def delete_document_if_exists(doc_id: str, collection_type: str = "team"):
    manager = QdrantCollectionManager(collection_type)
    client = manager.get_client()
    collection = manager.get_collection_name()
    uuid_id = str(uuid5(NAMESPACE_DNS, doc_id))
    try:
        client.delete(collection_name=collection, points_selector={"points": [uuid_id]})
        print(f"🗑️ 삭제 완료: {doc_id} (UUID: {uuid_id})")
    except Exception as e:
        print(f"❌ 삭제 중 오류 발생: {e}")

def get_vectorstore(collection_type: str) -> QdrantVectorStore:
    if collection_type == "team":
        collection_name = os.getenv("QDRANT_COLLECTION_TEAM", "github_docs_team")
    elif collection_type == "summary":
        collection_name = os.getenv("QDRANT_COLLECTION_SUMMARY", "summary_docs")
    else:
        raise ValueError(f"Unknown collection_type: {collection_type}")

    embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        encode_kwargs={"normalize_embeddings": True}
    )

    qdrant_client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )

    return QdrantVectorStore(
        client=qdrant_client,
        collection_name=collection_name,
        embedding=embedding_model,
        content_payload_key="document",
    )