# app/context_construction/question_router.py

# 질문 유형 분류 함수
def classify_question_type(question: str) -> str:
    question = question.lower()

    if "누가" in question or "담당" in question:
        return "owner"
    elif "이번주" in question or "언제" in question:
        return "timeline"
    else:
        return "summary"
