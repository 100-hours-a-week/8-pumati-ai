# app/github_crawling/vector_store.py

import os
from datetime import datetime
from uuid import uuid5, NAMESPACE_DNS
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams, Distance, PayloadSchemaType
    
)

# 기존 ChromaDB 관련 코드 제거 & Qdrant 설정으로 교체
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "github_docs")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# 디비 생성시 최초 1회만 실행
# # 1. 컬렉션이 존재하면 삭제
# if client.collection_exists(collection_name=QDRANT_COLLECTION):
#     client.delete_collection(collection_name=QDRANT_COLLECTION)

# # 2. 새 컬렉션 생성
# client.create_collection(
#     collection_name=QDRANT_COLLECTION,
#     vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
# )

# 필드별 인덱스 생성
# payload_schema 인자를 sync client가 허용하지 않아서 필드별 인덱스 수동 생성

client.create_payload_index(QDRANT_COLLECTION, field_name="project_id", field_schema=PayloadSchemaType.INTEGER)
client.create_payload_index(QDRANT_COLLECTION, field_name="team_id", field_schema=PayloadSchemaType.KEYWORD)
client.create_payload_index(QDRANT_COLLECTION, field_name="repo", field_schema=PayloadSchemaType.KEYWORD)
client.create_payload_index(QDRANT_COLLECTION, field_name="type", field_schema=PayloadSchemaType.KEYWORD)
client.create_payload_index(QDRANT_COLLECTION, field_name="weight", field_schema=PayloadSchemaType.FLOAT)
client.create_payload_index(QDRANT_COLLECTION, field_name="date", field_schema=PayloadSchemaType.TEXT)

def is_id_exists(doc_id: str) -> bool:
    uuid_id = str(uuid5(NAMESPACE_DNS, doc_id))  # 동일 방식으로 변환
    result = client.retrieve(collection_name=QDRANT_COLLECTION, ids=[uuid_id])
    return len(result) > 0

def store_document(text: str, metadata: dict, embedding: list, doc_id: str):
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
        "wiki": 0.7,
    }
    weight = default_weights.get(doc_type, 1.0)
    if "Home" in filename or "Vision" in filename:
        weight += 1.0
    if "프로젝트" in text or "서비스" in text:
        weight += 1.0
    metadata["weight"] = weight

    print("✅  저장 직전 metadata:", metadata)

    uuid_id = str(uuid5(NAMESPACE_DNS, doc_id))  # 문자열 doc_id → UUID 변환

    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[{
            "id": uuid_id,
            "vector": embedding,
            "payload": {
                "document": text,
                **metadata
            }
        }]
    )

def show_vector_summary():
    count = client.count(collection_name=QDRANT_COLLECTION).count
    print("📦 총 벡터 수:", count)

    results = client.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=3,
        with_payload=True
    )
    print("🔍 일부 문서 미리보기:")
    for point in results[0]:
        print("-", point.payload.get("document", "")[:120], "...")
