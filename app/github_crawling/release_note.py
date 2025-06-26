from app.github_crawling.vector_store import store_document
from app.model_inference.rag_chat_runner import embedding_model

text = """
Pumati 품앗이 V2 요약

1. 품앗이란?
Pumati는 카카오테크 부트캠프 교육생들을 위한 트래픽 품앗이 플랫폼으로, 단순 홍보가 아닌 서로 응원하고 직접 써보는 커뮤니티입니다.

2. V2 주요 업데이트
- AI 팀별 챗봇 ‘마티’ 추가  
  팀의 GitHub 활동을 기반으로 "이 팀은 어떤 프로젝트를 하나요?" 같은 질문에 응답하는 팀 전용 챗봇 기능이 추가되었습니다.
- AI 엠블럼 뱃지 생성 기능  
  AI가 팀 로고를 분석해 원형 뱃지를 생성해주며, 프로젝트 수정 페이지에서 수정도 가능합니다.
- 마이페이지 기능 오픈  
  회원 정보 조회 및 수정  
  팀 프로젝트별 품앗이 등수, 참여 횟수 확인  
  받은 품앗이 뱃지 리스트로 보기 (타 프로젝트에 품앗이를 하면 해당 팀에 우리 팀 뱃지가 전달됨)
- 사용자 피드백 반영  
  자신이 속한 프로젝트에는 품앗이 포인트가 오르지 않음  
  매주 월요일 오전 9시에 품앗이 수 초기화 (매주 새로운 1등 기회 제공)
"""

metadata = {
    "repo": "100-hours-a-week/8-pumati-release",
    "date": "2025-06-26",
    "project_id": 6,
    "team_id": "8",
    "type": "summary",
    "part": "RELEASE_NOTE",
    "weight": 3.0
}

doc_id = "summary-8-RELEASE_NOTE-06-26"

store_document(text.strip(), metadata, embedding_model, doc_id)

# PYTHONPATH=. python -u app/github_crawling/release_note.py