from fastapi import APIRouter, HTTPException, Request, responses
import logging
from dotenv import load_dotenv
from google.cloud import tasks_v2
import os
import json
import asyncio
import requests

from services.badge_service import BadgeService
from fast_api.schemas.badge_schemas import BadgeRequest

load_dotenv()
app_badge = APIRouter()
badge_service = BadgeService()

#추후 환경변수 등록 필요.
GCP_PROJECT_ID = "ktb8team-458916"#os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = "asia-southeast1"#os.getenv("ARTIFACT_REGISTRY_LOCATION")
GCP_QUEUE_NAME = "badge-queue"#os.getenv("GCP_QUEUE_NAME")
GCP_TARGET_URL = os.getenv("AI_SERVER_URL")  # 비동기 처리를 수행할 서버 url(AI서버)
BE_URL = os.getenv("BE_SERVER_URL")
GCP_SERVICE_ACCOUNT_EMAIL = os.getenv("GCP_SERVICE_EMAIL")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def enqueue_badge_task(data: dict) -> None:
    '''
    뱃지 task를 Cloud RUN에 등록하는 과정.
    추후 큐 새로 생성하여 등록하기.
    '''
    logger.info(f"댓글 생성 요청을 큐에 보냅니다. AI_server: {GCP_TARGET_URL}")
    logger.info(f"댓글 생성 요청을 큐에 보냅니다. BE_server: {BE_URL}")
    logger.info(f"현재 위치는 {GCP_LOCATION}입니다.")

    # 1) GCP Cloud Tasks 클라이언트 생성
    client = tasks_v2.CloudTasksClient() # Google Cloud Tasks 클라이언트 생성
    badge_parent = client.queue_path(GCP_PROJECT_ID, GCP_LOCATION, GCP_QUEUE_NAME) # 작업(Task)을 보낼 대상 큐 경로를 생성합니다
    try:
        #댓글 생성에 필요한 정보(body)를 JSON으로 준비함.
        task_payload = {
            "requestData": data
        } 

        ################################################
        #Cloud Tasks에 전송할 하나의 작업 정보임. 추후 재 작성할것.
        badge_task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST, # post요청을 보냄.
                "url": f"{GCP_TARGET_URL}/api/badges/enque", # post요청을 보낼 API서버 주소(AI서버)
                "headers": {"Content-Type": "application/json"}, 
                "body": json.dumps(task_payload).encode(),
                "oidc_token": {
                    "service_account_email": GCP_SERVICE_ACCOUNT_EMAIL  # ← google task가 요청을 처리할 수 있게 실행.
                }
            }
        }
        ##############################################
        response = client.create_task(parent=badge_parent, task=badge_task)
        logger.info(f" Task enqueued: {response.name}")

    except Exception as e:
        logger.error(f"[ERROR] payload 생성 실패: {e}", exc_info=True)


@app_badge.post("/api/badges/enque")
async def process_badge_task(task_request: Request) -> dict:
    logger.info("큐에 등록되었습니다.")
    # Cloud Tasks가 보낸 JSON body를 파싱 -> project_id, request_data를 가져옴.
    try:
        body = await task_request.json()
        request_data = body.get("requestData")

    except Exception as e:
        logger.error(f"[ERROR] request.json() 실패: {e}", exc_info=True)
        #raise HTTPException(status_code=400, detail="Invalid JSON")

    #값이 없을 경우, 400error 발생 -> 해당 내용 백엔드와 상의 필요.
    if not (request_data):
        raise HTTPException(status_code=400, detail="Invalid task payload")

    logger.info(f" Cloud Task 수신함.")

    try:
        badge_generate_instance = BadgeService()
        badge_URL = badge_generate_instance.generate_and_save_badge(team_number = request_data["teamNumber"] ,request_data = BadgeRequest(**request_data)) #request_data를 BadgeRequest형태로 변경하여 모델에 전달.

        #BE에 전달할 body
        payload = {
            "contentType" : badge_URL
        }

        teamId = {request_data["teamId"]}

        endpoint = f"{BE_URL}/api/teams/{teamId}/badge-image-url"
        response = requests.patch(endpoint, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        logger.info(f"댓글 전송 성공: {endpoint}, {payload}")
    except Exception as e:
        logger.error(f"댓글 생성/전송 중 에러 발생: {e}", exc_info=True) #traceback을 남김.

    return responses.JSONResponse(status_code=200, content={"status": "ok"})



async def prepare_response():
    return {
        "message": "requestReceived",
        "status": "pending"
    }


@app_badge.post("/api/badges/image")
async def receive_badge_request(badge_body: BadgeRequest):
    '''
    비동기 처리: 백엔드 응답 전송, 뱃지 생성 두가지 테스크를 비동기로 실행.
    '''
    logger.info(f"뱃지 생성 요청 수신")

    response, _ = await asyncio.gather(
        prepare_response(),
        enqueue_badge_task(badge_body.model_dump())
    )

    return response
