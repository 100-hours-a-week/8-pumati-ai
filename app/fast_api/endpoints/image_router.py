#image_router.py

from fastapi import APIRouter,responses #,Request, HTTPException, 
import logging
from dotenv import load_dotenv
import os
import asyncio
import requests
import json, time

from google.cloud import tasks_v2

from app.services.badge_service import BadgeService
from app.fast_api.schemas.badge_schemas import BadgeRequest, BadgeModifyRequest
from app.model_inference.loaders.badge_loader import badge_loader_instance

load_dotenv()
app_badge = APIRouter()
badge_service = BadgeService()

#추후 환경변수 등록 필요.
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("ARTIFACT_REGISTRY_LOCATION")
GCP_QUEUE_NAME = os.getenv("GCP_QUEUE_NAME")
GCP_TARGET_URL = os.getenv("AI_SERVER_URL")  # 비동기 처리를 수행할 서버 url(AI서버)
BE_URL = os.getenv("BE_SERVER_URL")
GCP_SERVICE_ACCOUNT_EMAIL = os.getenv("GCP_SERVICE_EMAIL")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def error_occured(team_info: dict):
    try:
        payload = {}
        teamId = team_info["teamId"]
        endpoint = f"{BE_URL}/api/teams/{teamId}/ai-badge-status"
        response = requests.patch(endpoint, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        logger.info(f"AI 서버 오류로 이미지 생성이 중단됩니다: {endpoint}")

    except Exception as e:
        logger.error(f"이미지 생성/전송 중 에러 발생: {e}", exc_info=True)

# async def enqueue_badge_task(mod_tags: str, team_info: dict) -> None:
#     '''
#     뱃지 task를 Cloud RUN에 등록하는 과정.
#     추후 큐 새로 생성하여 등록하기.
#     '''
#     logger.info("2-1) 큐 등록 요청 전송시작")
#     logger.info(f"이미지 생성 요청을 큐에 보냅니다. AI_server: {GCP_TARGET_URL}")
#     logger.info(f"이미지 생성 요청을 큐에 보냅니다. BE_server: {BE_URL}")
#     logger.info(f"현재 위치는 {GCP_LOCATION}입니다.")

#     # 1) GCP Cloud Tasks 클라이언트 생성
#     client = tasks_v2.CloudTasksClient() # Google Cloud Tasks 클라이언트 생성
#     badge_parent = client.queue_path(GCP_PROJECT_ID, GCP_LOCATION, GCP_QUEUE_NAME) # 작업(Task)을 보낼 대상 큐 경로를 생성합니다
#     try:
#         #이미지 생성에 필요한 정보(body)를 JSON으로 준비함.
#         logger.info("2-2) 큐 등록 요청 전송: payload 작성중")
#         task_payload = {
#             "modTags": mod_tags,
#             "requestData": team_info
#         } 

#         ################################################
#         #Cloud Tasks에 전송할 하나의 작업 정보임. 추후 재 작성할것. -> 작성 완료됨.
#         logger.info("2-3) 큐 등록 요청 전송: 큐 등록 Tasks 작성중")
#         badge_task = {
#             "http_request": {
#                 "http_method": tasks_v2.HttpMethod.POST, # post요청을 보냄.
#                 "url": f"{GCP_TARGET_URL}/api/badges/enque", # post요청을 보낼 API서버 주소(AI서버)
#                 "headers": {"Content-Type": "application/json"}, 
#                 "body": json.dumps(task_payload).encode(),
#                 "oidc_token": {
#                     "service_account_email": GCP_SERVICE_ACCOUNT_EMAIL  # ← google task가 요청을 처리할 수 있게 실행.
#                 }
#             }
#         }
#         ##############################################
#         logger.info("2-4) 큐 등록 요청 전송중.")
#         response = client.create_task(parent=badge_parent, task=badge_task)
#         logger.info(f" Task enqueued: {response.name}")

#     except Exception as e:
#         logger.error(f"[ERROR] payload 생성 실패: {e}", exc_info=True)
        


# @app_badge.post("/api/badges/enque")
# async def process_badge_task(task_request: Request) -> dict:
#     logger.info("3-1) 큐 등록 완료")
#     # Cloud Tasks가 보낸 JSON body를 파싱 -> project_id, request_data를 가져옴.
#     try:
#         body = await task_request.json()
#         mod_tags = body.get("modTags")
#         request_team_info = body.get("requestData")

#     except Exception as e:
#         logger.error(f"[ERROR] request.json() 실패: {e}", exc_info=True)
#         #raise HTTPException(status_code=400, detail="Invalid JSON")

#     #값이 없을 경우, 400error 발생 -> 해당 내용 백엔드와 상의 필요.
#     if not (request_team_info):
#         raise HTTPException(status_code=400, detail="Invalid task payload")

#     logger.info("3-2) 큐: 데이터 수신 완료")

#     try:
#         badge_generate_instance = BadgeService()
#         logger.info("3-3) 뱃지 생성을 시작중")
#         badge_URL = badge_generate_instance.generate_and_save_badge(mod_tags = mod_tags, team_number = request_team_info["teamNumber"] ,request_data = BadgeRequest(**request_team_info)) #request_data를 BadgeRequest형태로 변경하여 모델에 전달.

#         logger.info(f"9-1) BE 서버에 전송할 payload작성중...")
#         #BE에 전달할 body
#         payload = {
#             "badgeImageUrl" : badge_URL
#         }

        
#         teamId = request_team_info["teamId"]

#         endpoint = f"{BE_URL}/api/teams/{teamId}/badge-image-url"
#         logger.info(f"9-2) {endpoint}으로 patch요청")
#         response = requests.patch(endpoint, json=payload, headers={"Content-Type": "application/json"})
#         response.raise_for_status()
#         logger.info(f"9-3) 이미지 전송 성공: {endpoint}, {payload}")
#         logger.info(f"9-4) 서버를 종료합니다.")
#     except Exception as e:
#         logger.error(f"이미지 생성/전송 중 에러 발생: {e}", exc_info=True) #traceback을 남김.
#         await error_occured(request_team_info)

#     return responses.JSONResponse(status_code=200, content={"status": "ok"})

async def process_badge_task(mod_tags: str, team_info: dict) -> dict:
    logger.info("2-1) 비동기로 뱃지 생성을 시작중...")
    start = time.perf_counter()
    try:
        badge_generate_instance = BadgeService()
        logger.info("2-2) 뱃지 생성 요청중...")
        badge_URL = badge_generate_instance.generate_and_save_badge(mod_tags = mod_tags, team_number = team_info["teamNumber"] ,request_data = BadgeRequest(**team_info)) #request_data를 BadgeRequest형태로 변경하여 모델에 전달.

        logger.info(f"9-1) BE 서버에 전송할 payload작성중...")
        payload = {
            "badgeImageUrl" : badge_URL
        }
        teamId = team_info["teamId"]

        endpoint = f"{BE_URL}/api/teams/{teamId}/badge-image-url"
        logger.info(f"9-2) {endpoint}으로 patch요청")
        response = requests.patch(endpoint, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        logger.info(f"9-3) 이미지 전송 성공: {endpoint}, {payload}")
        logger.info(f"9-4) 서버를 종료합니다.")
        logger.info(f"9-5) 동작 시간: {time.perf_counter() - start}")
    except Exception as e:
        logger.error(f"이미지 생성/전송 중 에러 발생: {e}", exc_info=True) #traceback을 남김.
        logger.info(f"9-5) 동작 시간: {time.perf_counter() - start}")
        await error_occured(team_info)

    return responses.JSONResponse(status_code=200, content={"status": "ok"})



async def prepare_response():
    return {
        "message": "requestReceived",
        "status": "pending"
    }

# @app_badge.on_event("startup")
# async def load_model_on_startup():
#     try:
#         print("🚀 모델 로드 시작")
#         badge_loader_instance.load_diffusion_model()
#         print("✅ 모델 로드 성공")
#     except Exception as e:
#         print(f"❌ 모델 로드 실패: {e}")

# BE -> AI 요청 수락
@app_badge.post("/api/badges/image")
async def receive_badge_request(badge_body: BadgeRequest):
    '''
    비동기 처리: 백엔드 응답 전송, 뱃지 생성 두가지 테스크를 비동기로 실행.
    '''
    logger.info(f"1-1) 뱃지 생성 요청 수신. 수신된 데이터: {badge_body}")
    # teamId, teamNumber는 미리 빼서 전달

    response = await prepare_response()
    logger.info("1-2) 뱃지 생성을 비동기로 요청")
    asyncio.create_task(process_badge_task(mod_tags = None, team_info = badge_body.model_dump()))  # 이건 백그라운드에서 실행되고 안 기다림

    return response

@app_badge.put("/api/badges/image")
async def receive_badge_modi_request(badge_modi_body: BadgeModifyRequest):
    '''
    비동기 처리: 백엔드 응답 전송, 뱃지 생성 두가지 테스크를 비동기로 실행.
    '''
    logger.info(f"1-1) 뱃지 수정 요청 수신. 수신된 데이터: {badge_modi_body}")

    # mod_tags, team_info로 미리 빼서 전달
    mod_tags = badge_modi_body.modificationTags[0]
    team_info = badge_modi_body.projectSummary

    response = await prepare_response()

    logger.info("1-2) 뱃지 수정을 비동기로 요청")
    asyncio.create_task(process_badge_task(mod_tags = mod_tags, team_info = team_info.model_dump()))  # 이건 백그라운드에서 실행되고 안 기다림

    return response
