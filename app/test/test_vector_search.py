# app/test/test_vector_search.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from context_construction.vector_search import search_similar_docs
# from app.context_construction.vector_search import search_similar_docs

if __name__ == "__main__":
    question = "어떤 기능이 있어?"
    team_id = "100-hours-a-week/8-pumati-ai"

    print(f"🔍 질문: {question}")
    print(f"🔍 팀 ID: {team_id}")

    docs, metas, scores = search_similar_docs(question, team_id, top_k=3)

    # vector_search.py 내부
    print(f"[DEBUG] 검색 대상 팀 ID: {team_id}")
    print(f"[DEBUG] 검색 질문: {question}")
    # print(f"[DEBUG] 결과: {results}")

    if not docs:
        print("⚠️ 검색 결과 없음")
    else:
        for i, (doc, meta, score) in enumerate(zip(docs, metas, scores), 1):
            print(f"\n🔎 [{i}] {meta['date']} / score: {score:.4f}")
            print(f"📄 {doc}")