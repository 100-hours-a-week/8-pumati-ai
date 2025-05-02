from fastapi import FastAPI, BackgroundTasks
from dotenv import load_dotenv
import requests
import os

from app.model_inference.loaders.gemma_loader import GemmaModel
from app.fast_api.schemas.comment_schemas import CommentRequest

########################
# 서버 설정
########################
load_dotenv()
comment_app = FastAPI()
RECEIVER_API_BASE_URL = os.getenv("RECEIVER_API_URL", "https://abcd1234.ngrok.io") #백엔드 주소 입력.


@comment_app.get("/")
def root():
    return {"message": "FastAPI is running. Model loaded..."}

# 백그라운드에서 실행될 댓글 생성 및 전송 로직
def generate_and_send(project_id: str, request_data: CommentRequest):
    try:
        # 모델 로드 및 준비
        gemma = GemmaModel(request_data)
        gemma.load_gemma()

        for i in range(4):
            author_name = gemma.fake_name
            author_nickname = gemma.fake_nickname

            generated_comment = gemma.model_inference()

            payload = {
                "content": generated_comment,
                "authorName": author_name,
                "authorNickname": author_nickname
            }

            headers = {"Content-Type": "application/json"} #Json 데이터 전송 예정.

            endpoint = f"{RECEIVER_API_BASE_URL}/api/projects/{project_id}/ai-comments"
            response = requests.post(endpoint, json=payload, headers=headers)

            print("댓글 전송 성공:")
            print(payload, response.status_code)

    except Exception as e:
        print(f"댓글 생성 또는 전송 실패: {str(e)}")


# FastAPI endpoint: 외부 백엔드가 호출하는 진입점
#project_id : 문자열로 각 팀 번호가 전달됨.
@comment_app.post("/api/generate-comment/{project_id}")
async def receive_generate_request(project_id: str, request: CommentRequest, background_tasks: BackgroundTasks):
    print(f"댓글 요청 수신 - project_id: {project_id}")

    # 비동기 처리 시작
    background_tasks.add_task(generate_and_send, project_id, request)

    # 요청은 먼저 잘 받았다고 바로 응답
    return {
        "status": "accepted",
        "message": f"댓글 생성을 시작했어요. project_id={project_id}"
    }
