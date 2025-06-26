# app/github_crawling/vector_store.py

import os
from uuid import uuid5, NAMESPACE_DNS
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PayloadSchemaType
from uuid import uuid5, NAMESPACE_DNS
from app.github_crawling.embedding import get_embedding

# 기존 ChromaDB 관련 코드 제거 & Qdrant 설정으로 교체
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "github_docs")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

if not client.collection_exists(collection_name=QDRANT_COLLECTION):
    print(f"✨ '{QDRANT_COLLECTION}' 컬렉션이 존재하지 않아 새로 생성합니다.")
    
    # 컬렉션 생성
    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
    )

    # 필드별 인덱스 생성
    # payload_schema 인자를 sync client가 허용하지 않아서 필드별 인덱스 수동 생성
    client.create_payload_index(QDRANT_COLLECTION, field_name="project_id", field_schema=PayloadSchemaType.INTEGER)
    client.create_payload_index(QDRANT_COLLECTION, field_name="team_id", field_schema=PayloadSchemaType.INTEGER)
    client.create_payload_index(QDRANT_COLLECTION, field_name="repo", field_schema=PayloadSchemaType.KEYWORD)
    client.create_payload_index(QDRANT_COLLECTION, field_name="type", field_schema=PayloadSchemaType.KEYWORD)
    client.create_payload_index(QDRANT_COLLECTION, field_name="weight", field_schema=PayloadSchemaType.FLOAT)
    client.create_payload_index(QDRANT_COLLECTION, field_name="date", field_schema=PayloadSchemaType.TEXT)

else:
    print(f"➡️ '{QDRANT_COLLECTION}' 컬렉션이 이미 존재합니다. 생성을 생략합니다.")

def is_id_exists(doc_id: str) -> bool:
    uuid_id = str(uuid5(NAMESPACE_DNS, doc_id))  # 동일 방식으로 변환
    result = client.retrieve(collection_name=QDRANT_COLLECTION, ids=[uuid_id])
    return len(result) > 0

def store_document(text, metadata, embedding_model, doc_id):
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

    # 텍스트 내용 기반 추가 가중치
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
        doc = point.payload.get("document", "")
        if isinstance(doc, str):
            print("-", doc[:120], "...")
        else:
            print("-", str(doc), "...")

def delete_document_if_exists(doc_id: str):
    """doc_id(문자열)를 기반으로 Qdrant에서 해당 UUID 벡터를 삭제"""
    uuid_id = str(uuid5(NAMESPACE_DNS, doc_id))  # 동일한 UUID 방식 적용
    try:
        client.delete(collection_name=QDRANT_COLLECTION, points_selector={"points": [uuid_id]})
        print(f"🗑️ 삭제 완료: {doc_id} (UUID: {uuid_id})")
    except Exception as e:
        print(f"❌ 삭제 중 오류 발생: {e}")