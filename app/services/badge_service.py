#badge_service.py

import os, math
import requests
from io import BytesIO
from typing import List
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import logging

from app.fast_api.schemas.badge_schemas import BadgeRequest
from app.model_inference.badge_inference_runner import generate_image

BE_SERVER = os.getenv("BE_SERVER_URL")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class BadgeService:
    def __init__(self):
        pass

    def create_url(self, image_bytes: BytesIO, team_number: int) -> str:
        # 0) 변수 정의
        file_name = f"badge_image_{team_number}.png"
        content_type = "image/png"

        # 1) Pre-signed URL 요청
        logger.info("7-2) Presigned URL 요청")
        logger.info(f"7-3) {BE_SERVER}/api/pre-signed-url으로 post요청중...")
        response = requests.post(f"{BE_SERVER}/api/pre-signed-url", json={
            "fileName": file_name,
            "contentType": content_type
        })

        # 1-1) 예외처리
        if response.status_code != 201:
            raise Exception(f"Pre-signed URL 발급 실패: {response.text}")

        logger.info("7-4) S3에 이미지 업로드 중...")
        upload_data = response.json()["data"]
        upload_url = upload_data["uploadUrl"]
        public_url = upload_data["publicUrl"]

        # 2. S3에 PUT으로 이미지 업로드
        logger.info(f"7-5) {upload_url}에 put요청.")
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

        logger.info(f"7-6) S3에 업로드 성공")
        return public_url 

    def draw_rotated_text(self, base_image, draw_center, radius, text, total_angle=90, start_angle=-90):
        chars = list(text)

        thresholds = [6, 9, 12, 15]
        angles = [60, 90, 120, 150]

        for t, a in zip(thresholds, angles):
            if len(chars) - 1 < t:
                total_angle = a
                break
        else:
            total_angle = 180

        font = ImageFont.truetype("./app/utils/Pretendard-Black.ttf", 35)
        angle_step = total_angle / (len(chars) - 1) if len(chars) > 1 else 0
        base_angle = start_angle - total_angle / 2 #첫 글자의 위치(+는 시계방향, -는 반시계방향임.)

        # 각 글자를 알맞은 각도에 맞게 돌리기.
        for i, ch in enumerate(chars):
            angle_deg = base_angle + i * angle_step 
            angle_rad = math.radians(angle_deg)
            x = draw_center[0] + int(radius * math.cos(angle_rad))
            y = draw_center[1] + int(radius * math.sin(angle_rad))

            dx = abs(draw_center[0] - x)
            dy = abs(draw_center[1] - y)
            base_rotation = np.rad2deg(np.arctan2(dx, dy))

            if i < len(text) // 2:
                rotation = base_rotation
            else:
                rotation = - base_rotation

            char_img = Image.new("RGBA", (50, 50), (255, 255, 255, 0))  # 완전 투명 배경, text의 기본 틀
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((25, 25), ch, font=font, fill=(0, 0, 0, 255), anchor="mm") #(255, 215, 0, 255)

            rotated_char = char_img.rotate(rotation, center=(25, 25), resample=Image.Resampling.BICUBIC)
            base_image.paste(rotated_char, (x - 25, y - 25), rotated_char)

        return base_image

    def generate_and_save_badge(self, mod_tags: str, team_number: int, request_data: BadgeRequest):
        '''
        BadgeService의 메인 기능.
        '''
        logger.info("3-1) badge 이미지 생성 시작")
        # 1) 이미지 생성하기
        image = generate_image(mod_tags, team_number, request_data)

        # 2) 팀 title 입력
        #logger.info("7-1) teamtitle 붙여주기")
        #image_final = self.draw_rotated_text(image, (256, 256), 180, request_data.title)

        logger.info("7-1) Presigned URL 가져오기")
        # 3) 이미지 메모리 스트림 변환
        with BytesIO() as image_bytes:
            image.save(image_bytes, format="PNG")
            image_bytes.seek(0)
            # 4) S3에 저장 후 url 반환받기
            public_url = self.create_url(image_bytes, team_number)

        return public_url


