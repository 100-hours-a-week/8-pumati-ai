from fastapi import APIRouter, HTTPException, Request
from dotenv import load_dotenv
from faker import Faker
import os
import logging
import json
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from datetime import datetime, timezone
import requests
import random

from model_inference.loaders.comment_loader import clovax_model_instance
from fast_api.schemas.comment_schemas import CommentRequest

# ------------------------------
# 설정
# ------------------------------
load_dotenv()
comment_app = APIRouter()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

COMMENT_GENERATE_COUNT = 4
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("ARTIFACT_REGISTRY_LOCATION")
GCP_QUEUE_NAME = os.getenv("GCP_QUEUE_NAME")
GCP_TARGET_URL = os.getenv("AI_SERVER_URL")  # 비동기 처리를 수행할 서버 url(AI서버)
BE_URL = os.getenv("BE_SERVER_URL")
GCP_SERVICE_ACCOUNT_EMAIL = os.getenv("GCP_SERVICE_EMAIL")


@comment_app.get("/")
def root():
    return {"message": "FastAPI is running. Model loaded..."}


# ------------------------------
# 댓글 생성 요청 → Cloud Tasks 큐에 등록
# 백그라운드에서 댓글 생성 작업을 비동기로 처리하기 위함
# ------------------------------
def enqueue_comment_task(project_id: str, request_data: dict) -> None: #, post_url: str):
    logger.info(f"댓글 생성 요청을 큐에 보냅니다. AI_server: {GCP_TARGET_URL}")
    logger.info(f"댓글 생성 요청을 큐에 보냅니다. BE_server: {BE_URL}")
    try:
        client = tasks_v2.CloudTasksClient() # Google Cloud Tasks 클라이언트 생성
        parent = client.queue_path(GCP_PROJECT_ID, GCP_LOCATION, GCP_QUEUE_NAME) # 작업(Task)을 보낼 대상 큐 경로를 생성합니다
        logger.info(f"현재 위치는 {GCP_LOCATION}입니다.")

        task_payload = {
            "projectId": project_id,
            "requestData": request_data
        } #댓글 생성에 필요한 정보를 JSON으로 준비함.

        #Cloud Tasks에 등록할 하나의 작업 정보임.
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST, # post요청을 보냄.
                "url": f"{GCP_TARGET_URL}/api/tasks/process-comment", # post요청을 보낼 API서버 주소(AI서버)
                "headers": {"Content-Type": "application/json"}, 
                "body": json.dumps(task_payload).encode(),
                "oidc_token": {
                    "service_account_email": GCP_SERVICE_ACCOUNT_EMAIL  # ← google task가 요청을 처리할 수 있게 실행.
                }
            }
        }
    except Exception as e:
        logger.error(f"[ERROR] payload 생성 실패: {e}", exc_info=True)
        #raise HTTPException(status_code=400, detail="Invalid JSON")

    # Optional: 지연 시간 설정 (즉시 실행 시 생략) -> 즉시 실행으로 설정함.
    now = datetime.now(timezone.utc)
    timestamp = timestamp_pb2.Timestamp()
    timestamp.FromDatetime(now)
    task["schedule_time"] = timestamp

    response = client.create_task(parent=parent, task=task)
    logger.info(f" Task enqueued: {response.name}")


# ------------------------------
# 외부에서 호출되는 Cloud Tasks 수신 처리 엔드포인트
# ------------------------------
@comment_app.post("/api/tasks/process-comment")
async def process_comment_task(request: Request) -> dict:
    logger.info("큐에 등록되었습니다.")
    # Cloud Tasks가 보낸 JSON body를 파싱 -> project_id, request_data를 가져옴.
    try:
        body = await request.json()
        project_id = body.get("projectId")
        request_data = body.get("requestData")

    except Exception as e:
        logger.error(f"[ERROR] request.json() 실패: {e}", exc_info=True)
        #raise HTTPException(status_code=400, detail="Invalid JSON")

    #####################값이 없을 경우, 400error 발생 -> 해당 내용 백엔드와 상의 필요.
    if not (project_id and request_data):
        raise HTTPException(status_code=400, detail="Invalid task payload")

    logger.info(f" Cloud Task 수신: project_id={project_id}")

    #댓글을 4번 생성하기 위한 루프
    for _ in range(COMMENT_GENERATE_COUNT):
        try:
            fake_en = Faker()
            fake_ko = Faker('ko_KR')
            # 성별 결정
            gender = random.choice(["male", "female"])

            if gender == "male":
                author_name = fake_en.first_name_male()
                author_nickname = fake_ko.name_male()
            else:
                author_name = fake_en.first_name_female()
                author_nickname = fake_ko.name_female()

            generated_comment = clovax_model_instance.generate_comment(CommentRequest(**request_data)) #request_data를 CommentRequest형태로 변경하여 모델에 전달.

            payload = {
                "content": json.dumps(generated_comment, ensure_ascii=False)[1:-1],
                "authorName": author_name,
                "authorNickname": author_nickname
            }

            endpoint = f"{BE_URL}/api/projects/{project_id}/comments/ai"
            response = requests.post(endpoint, json=payload, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            logger.info(f"댓글 전송 성공: {endpoint}, {payload}")
        except Exception as e:
            logger.error(f"댓글 생성/전송 중 에러 발생: {e}", exc_info=True) #traceback을 남김.

    return {"status": "success"}


# ------------------------------
# 최초 댓글 생성 요청 → Cloud Tasks로 전달
# ------------------------------
@comment_app.post("/api/projects/{project_id}/comments")
async def receive_generate_request(project_id: str, request_data: CommentRequest, request: Request):
    logger.info(f"댓글 생성 요청 수신 - project_id: {project_id}")
    #post_url = f"http://{request.client.host}:{request.client.port}"

    #logger.info(f"댓글 생성 요청 수신 - BE_url: {post_url}")

    enqueue_comment_task(project_id, request_data.model_dump())#, post_url)

    return {
        "message": "requestGenerateCommentsSuccess",
        "data": {
            "status": "pending"
        }
    }
