import os
import requests
from io import BytesIO
from typing import List

from app.fast_api.schemas.badge_schemas import BadgeRequest
from app.model_inference.badge_inference_runner import generate_image

BE_SERVER = os.getenv("BE_SERVER_URL")

class BadgeService:
    def __init__(self):
        pass

    def create_url(self, image_bytes: BytesIO, team_number: int) -> str:
        # 0) 변수 정의
        file_name = f"badge_image_{team_number}"
        content_type = "image/png"

        # 1) Pre-signed URL 요청
        response = requests.post(f"{BE_SERVER}/api/pre-signed-url", json={
            "fileName": file_name,
            "contentType": content_type
        })

        # 1-1) 예외처리
        if response.status_code != 201:
            raise Exception(f"Pre-signed URL 발급 실패: {response.text}")

        upload_data = response.json()["data"]
        upload_url = upload_data["uploadUrl"]
        public_url = upload_data["publicUrl"]

        # 2. S3에 PUT으로 이미지 업로드
        upload_response = requests.put(
            upload_url,
            data=image_bytes.getvalue(),
            headers={
                "Content-Type": content_type,
                "x-amz-acl": "public-read"
            }
        )

        # 2-1) 예외처리
        if upload_response.status_code != 200:
            raise Exception(f"S3 업로드 실패: {upload_response.text}")

        return public_url 

    def generate_and_save_badge(self, mod_tags: List[str], team_number: int, request_data: BadgeRequest):
        '''
        BadgeService의 메인 기능.
        '''
        # 1) 이미지 생성하기
        image = generate_image(mod_tags, team_number, request_data)

        # 2) 이미지 메모리 스트림 변환
        with BytesIO() as image_bytes:
            image.save(image_bytes, format="PNG")
            image_bytes.seek(0)
            public_url = self.create_url(image_bytes, team_number)

        # 3) S3에 저장 후 url 반환받기
        public_url = self.create_url(image_bytes, team_number)

        return public_url


