from fastapi import APIRouter, BackgroundTasks
from dotenv import load_dotenv
from faker import Faker
import requests
import os
import logging

from app.model_inference.loaders.gemma_loader import gemma_model_instance
from app.fast_api.schemas.comment_schemas import CommentRequest

########################
# 서버 설정
########################
load_dotenv()
comment_app = APIRouter()
logger = logging.getLogger(__name__)
RECEIVER_API_BASE_URL = os.getenv("RECEIVER_API_URL", "https://abcd1234.ngrok.io") #백엔드 주소. 환경변수에 입력됨.
COMMENT_GENERATE_COUNT = 4


@comment_app.get("/")
def root():
    return {"message": "FastAPI is running. Model loaded..."}

# 백그라운드에서 실행될 댓글 생성 및 전송 로직
def generate_and_send(project_id: str, request_data: CommentRequest):
    try:
        for _ in range(COMMENT_GENERATE_COUNT):
            fake = Faker()
            fake_ko = Faker('ko_KR')
            author_name = fake.first_name()
            author_nickname = fake_ko.name()

            generated_comment = gemma_model_instance.generate_comment(request_data)

            payload = {
                "content": generated_comment,
                "authorName": author_name,
                "authorNickname": author_nickname
            }

            headers = {"Content-Type": "application/json"} #Json 데이터 전송 예정.

            endpoint = f"{RECEIVER_API_BASE_URL}/api/projects/{project_id}/ai-comments"
            response = requests.post(endpoint, json=payload, headers=headers)

            if response.status_code != 200:
                logger.warning(f"댓글 전송 실패: {response.status_code} - {response.text}")
            else:
                logger.info(f"댓글 전송 성공: {payload}")

    except Exception as e:
        logger.error("댓글 생성 또는 전송 실패", exc_info=True)


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
