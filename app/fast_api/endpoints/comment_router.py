from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from dotenv import load_dotenv
from faker import Faker
import requests
import os
import logging
import json
from enum import Enum

from model_inference.loaders.comment_loader import clovax_model_instance
from fast_api.schemas.comment_schemas import CommentRequest

# ------------------------------
# 설정
# ------------------------------
load_dotenv()
comment_app = APIRouter()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

#RECEIVER_API_BASE_URL = "http://0.0.0.0:9000" os.getenv("RECEIVER_API_URL", "https://abcd1234.ngrok.io")
COMMENT_GENERATE_COUNT = 4


@comment_app.get("/")
def root():
    return {"message": "FastAPI is running. Model loaded..."}


# ------------------------------
# 댓글 생성 및 전송 함수 
# ------------------------------
def generate_comment_payload(request_data: CommentRequest) -> dict:
    fake = Faker()
    fake_ko = Faker('ko_KR')

    author_name = fake.first_name()
    author_nickname = fake_ko.name()
    generated_comment = clovax_model_instance.generate_comment(request_data)

    return {
        "content": json.dumps(generated_comment, ensure_ascii=False)[1:-1],
        "authorName": author_name,
        "authorNickname": author_nickname
    }


def send_comment_to_backend(project_id: str, payload: dict) -> None: #, post_url: str)
    endpoint = f"https://bd48-211-244-225-166.ngrok-free.app/api/projects/{project_id}/comments" #f"{post_url}/api/projects/{project_id}/ai-comments"
    logger.info(f"실제 endpoint: {endpoint}")
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"댓글 전송 성공: {payload}")

    except requests.RequestException as e:
        logger.error(f"댓글 전송 실패: {e}")
        raise


def generate_and_send_comments(project_id: str, request_data: CommentRequest) -> None: #, post_url: str)
    for _ in range(COMMENT_GENERATE_COUNT):
        try:
            payload = generate_comment_payload(request_data)
            send_comment_to_backend(project_id, payload)#, post_url)
#
        except Exception as e:
            logger.error(f"댓글 생성/전송 중 에러 발생: {e}", exc_info=True)


# ------------------------------
# API 엔드포인트
# ------------------------------


class CommentStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    FAILED = "failed"


@comment_app.post("/api/projects/{project_id}/comments")
async def receive_generate_request(project_id: str, request_data: CommentRequest, background_tasks: BackgroundTasks, request: Request):
    logger.info(f"댓글 생성 요청 수신 - project_id: {project_id}")

    post_url = f"http://{request.client.host}:{request.client.port}"

    # 비동기로 댓글 생성 및 전송 시작
    background_tasks.add_task(generate_and_send_comments, project_id, request_data) #, post_url)

    # 백엔드에 요청받는 즉시 응답.
    status = CommentStatus.PENDING
    response = {
        "message": "requestGenerateCommentsSuccess",
        "data": {
            "status": status
        }
    }

    return response

"""

{
      "message": "requestGenerateCommentsSuccess",
      "data": {
          "status": "pending"
      }
}
"""
