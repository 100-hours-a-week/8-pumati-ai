# app/context_construction/question_router.py

# 질문이 구조화된 질문인지 여부
def is_structured_question(question: str) -> bool:
    question = question.lower()
    return any(kw in question for kw in ["누가", "담당", "이번주", "언제", "어떤 프로젝트", "무슨 기능", "어떤 기능"])

# 정형 질문이면 타입 분류
def classify_question_type(question: str) -> str:
    question = question.lower()
    print(f"[분류 대상 질문] {question}")
    
    if "누가" in question or "담당" in question:
        print("→ owner")
        return "owner"
    elif "이번주" in question or "언제" in question:
        print("→ timeline")
        return "timeline"
    elif "어떤 프로젝트" in question:
        print("→ project")
        return "project"
    elif "어떤 기능" in question or "무슨 기능" in question:
        print("→ function")
        return "function"
    else:
        print("→ summary")
        return "summary"