from fastapi import APIRouter,Request, responses
import logging
from dotenv import load_dotenv
import os
import asyncio
import requests

from app.services.badge_service import BadgeService
from app.fast_api.schemas.badge_schemas import BadgeRequest, BadgeModifyRequest

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

async def process_badge_task(mod_tags, team_info: Request) -> dict:
    try:
        teamId = team_info["teamId"]
        teamNumber = team_info["teamNumber"]

        ## 추후 수정 코드를 추가할 것.
        badge_URL = badge_service.generate_and_save_badge(mod_tags = mod_tags, team_number = teamNumber ,request_data = BadgeRequest(**team_info)) #request_data를 BadgeRequest형태로 변경하여 모델에 전달.

        #BE에 전달할 body
        payload = {
            "badgeImageUrl" : badge_URL
        }

        endpoint = f"{BE_URL}/api/teams/{teamId}/badge-image-url"
        response = requests.patch(endpoint, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        logger.info(f"이미지 전송 성공: {endpoint}, {payload}")
        
    except Exception as e:
        logger.error(f"이미지 생성/전송 중 에러 발생: {e}", exc_info=True) #traceback을 남김.

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
    logger.info(f"뱃지 생성 요청 수신. 수신된 데이터: {badge_body}")
    # teamId, teamNumber는 미리 빼서 전달


    response, _ = await asyncio.gather(
        prepare_response(),
        process_badge_task(mod_tags = None, team_info = badge_body.model_dump())
    )

    return response

@app_badge.put("/api/badges/image")
async def receive_badge_modi_request(badge_modi_body: BadgeModifyRequest):
    '''
    비동기 처리: 백엔드 응답 전송, 뱃지 생성 두가지 테스크를 비동기로 실행.
    '''
    logger.info(f"뱃지 수정 요청 수신. 수신된 데이터: {badge_modi_body}")

    # teamId, teamNumber는 미리 빼서 전달
    mod_tags = badge_modi_body.modificationTags
    team_info = badge_modi_body.projectSummary

    response, _ = await asyncio.gather(
        prepare_response(),
        process_badge_task(mod_tags = mod_tags, team_info = team_info.model_dump())
    )

    return response
