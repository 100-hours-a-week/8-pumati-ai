# /Users/minsun/Desktop/8-pumati-ai/app/test/chatbot_eval.py

import os
import csv
import time
from dotenv import load_dotenv
import google.generativeai as genai

from app.model_inference.rag_chat_runner import run_rag

# 🔐 환경 변수 로드
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Gemini 평가 함수
def evaluate_with_gemini(question, answer, context, eval_type="accuracy"):
    if eval_type == "accuracy":
        prompt = f"""
다음은 사용자 질문, 챗봇 응답, 그리고 문서 내용입니다.
챗봇 응답이 문서에 기반해 사실에 맞게 작성되었는지 평가하세요.
문서에 없는 내용을 포함하거나 잘못된 정보를 담고 있다면 "False",
문서 내용과 일치하고 허위 정보가 없다면 "True"만 출력하세요.

질문:
{question}

챗봇 응답:
{answer}

문서 내용:
{context}

정답:
"""
    elif eval_type == "conciseness":
        prompt = f"""
다음은 사용자 질문과 챗봇 응답입니다.
챗봇 응답이 얼마나 간결하게 핵심만 요약했는지를 1~5점으로 평가하세요.

- 매우 간결하면 5점
- 장황하거나 반복되는 말이 많으면 1점입니다.

질문:
{question}

챗봇 응답:
{answer}

정답 (1~5 중 하나의 숫자만 작성):
"""
    else:
        raise ValueError("지원하지 않는 평가 유형입니다: accuracy 또는 conciseness 중 선택하세요.")

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt.strip())
    result = response.text.strip()
    time.sleep(1)  # ✅ 과금 방지를 위한 sleep

    return result

# ✅ 전체 평가 실행 함수
def evaluate_questions_from_csv(csv_path, project_id=1, output_path="rag_eval_result.csv"):
    results = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            question = row["question"]
            context = row["ground_truth"]

            print(f"\n🧪 질문: {question}")

            # 🔁 챗봇 응답 생성
            answer = run_rag(question, project_id=project_id)
            print(f"🤖 응답: {answer}")

            # 🔁 평가 수행
            accuracy_eval = evaluate_with_gemini(question, answer, context, "accuracy")
            conciseness_eval = evaluate_with_gemini(question, answer, context, "conciseness")

            print(f"✅ 정확성 평가: {accuracy_eval} / 간결성 평가: {conciseness_eval}")

            results.append({
                "question": question,
                "chatbot_answer": answer,
                "ground_truth": context,
                "accuracy_eval": accuracy_eval,
                "conciseness_eval": conciseness_eval
            })

    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\n🎉 평가 완료 → 결과 저장: {output_path}")
    return output_path

# ✅ 실행 엔트리포인트
if __name__ == "__main__":
    evaluate_questions_from_csv("questions.csv", project_id=1)
