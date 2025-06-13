from app.fast_api.schemas.badge_schemas import BadgeRequest

from deep_translator import GoogleTranslator
from typing import List
import numpy as np
from PIL import Image, ImageDraw, ImageFont #새로 추가됨.
import math, json
import cv2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import BytesIO
from collections import Counter

import logging, os, stat, tempfile, subprocess

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class BadgePrompt:
    def __init__(self, data: BadgeRequest):
        self.data = data
        self.color= None
    
    def generate_corrected_badge(self, number: int, image_size: int = 800):
        center = (image_size // 2, image_size // 2)
        outer_radius = 350
        inner_radius = 240

        # 1. 흰 배경 생성
        base = Image.new("L", (image_size, image_size), 255)
        draw = ImageDraw.Draw(base)

        # 2. 전체 외곽 원 (250px) - 삭제되지 않음
        def draw_full_circle(draw_obj, radius, thickness=6):
            for angle in range(0, 360):
                theta = math.radians(angle)
                x = center[0] + int(radius * math.cos(theta))
                y = center[1] + int(radius * math.sin(theta))
                draw_obj.ellipse((x - thickness, y - thickness, x + thickness, y + thickness), fill=0)

        draw_full_circle(draw, outer_radius)

        # 3. 중간/내부 원 - 상단 90도만 그리기 (45도~135도)
        def draw_top_arc(draw_obj, radius, keep_start=-150 , keep_end=-30, thickness=1): #(-210, 30), (-245, 65), (-150,-30)
            for angle in range(keep_start, keep_end):
                theta = math.radians(angle)
                x = center[0] + int(radius * math.cos(theta))
                y = center[1] + int(radius * math.sin(theta))
                draw_obj.ellipse((x - thickness, y - thickness, x + thickness, y + thickness), fill=0)

        draw_top_arc(draw, inner_radius)

        # 4. 숫자 텍스트 삽입
        number_font = ImageFont.truetype("./app/utils/Pretendard-Black.ttf", 100)
        number_text = str(number)
        bbox = draw.textbbox((0, 0), number_text, font=number_font)
        text_width, _ = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((center[0] - text_width // 2, center[1] + outer_radius - 130), number_text, fill=0, font=number_font) 


        # 5. Canny 엣지 적용 및 저장
        cv_image = np.array(base)
        canny_image = cv2.Canny(cv_image, 30, 100)
        logger.info("4-3) Canny이미지 배경 생성 완료")
        return canny_image


    def load_css3_colors(self, path="css3_colors.json"):
        with open(path, "r") as f:
            return json.load(f)

    def closest_css3_color_name(self, rgb, css3_colors):
        min_dist = float('inf')
        closest_name = None

        for name, value in css3_colors.items():
            # value는 [R, G, B]
            dist = sum((c1 - c2) ** 2 for c1, c2 in zip(rgb, value))
            if dist < min_dist:
                min_dist = dist
                closest_name = name

        return closest_name
    
    def get_image(self, url):
        response = requests.get(url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        # plt.imshow(img)  
        # plt.show()
        small_img = img.resize((64, 64))  # 너무 작게는 하지 말기

        # 색상 목록 추출 (flatten)
        pixels = list(small_img.getdata())

        # 가장 많이 쓰인 색 찾기
        color_counts = Counter(pixels)
        most_common_colors = color_counts.most_common(3)
        css3_colors = self.load_css3_colors("./app/utils/css3_colors.json")
        color_names = [self.closest_css3_color_name(rgb, css3_colors) for rgb, _ in most_common_colors]
        # 색상명 리스트 추출  # 예: ['red', 'lime', 'blue']
        self.color = ', '.join(color_names)

        cv_image_logo = np.array(img)
        canny_logo = cv2.Canny(cv_image_logo, 50, 150)
        return canny_logo

    def get_disquiet_exact_team_image(self, team_title: str):
        logger.info("4-4) 각 팀의 로고 찾는 중...")
        url = f"https://disquiet.io/product/{team_title}"
        page_url = self.data.deploymentUrl 

        # options = Options()
        # options.add_argument("--headless")
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        options = Options()
        #options.binary_location = '/usr/bin/chronium-browser'
        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument("--headless")  # GUI 없이 실행
        options.add_argument("--no-sandbox")  # 권한 문제 회피
        options.add_argument("--disable-dev-shm-usage")  # 공유 메모리 문제 회피
        options.add_argument("--disable-gpu")  # GPU 비활성화 (optional)
        options.add_argument("--single-process")
        options.add_argument("--remote-debugging-port=9222")  # DevToolsActivePort 에러 방지
        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_argument('--disable-dev-shm-usage')

        logger.info("4-5) 크롬 트라이버 생성중...")
        with tempfile.TemporaryDirectory() as user_data_dir:
            options.add_argument(f'--user-data-dir={user_data_dir}')
            service = Service("/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)

        
        # driver_path = #ChromeDriverManager(driver_version="137.0.7151.70").install()
        # os.chmod(driver_path, stat.S_IRWXU)
        # service = Service(driver_path)

        # import subprocess
        # def get_chromedriver_version(driver_path):
        #     try:
        #         result = subprocess.run(
        #             [driver_path, '--version'],
        #             stdout=subprocess.PIPE,
        #             stderr=subprocess.PIPE,
        #             check=True,
        #             text=True
        #         )
        #         version = result.stdout.strip()
        #         return version
        #     except Exception as e:
        #         logging.error(f"chromedriver 버전 확인 실패: {e}")
        #         return None

        # version = get_chromedriver_version(driver_path)
        # logger.info(f"실제 사용 중인 chromedriver 버전: {version}")
        # driver = webdriver.Chrome(service=service, options=options)

        #version = get_chromedriver_version(driver_path)
        #logger.info(f"사용 중인 chromedriver 버전: {version}")
        #driver = webdriver.Chrome(service=service, chrome_options=chrome_options)
        #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(page_url)
        time.sleep(3)  # JS 렌더링 대기
        logger.info("4-6) 크롬 접속 가능함")

        try:
            resp = requests.get(page_url)
            soup = BeautifulSoup(resp.text, "html.parser")

            # 1. <link rel="icon"> 또는 <link rel="shortcut icon">
            icon_link = soup.find("link", rel=lambda x: x and "icon" in x)
            if icon_link and icon_link.get("href"):
                logger.info("4-7) 팀 파비콘 있음.")
                favicon_url = urljoin(page_url, icon_link["href"])
                canny_logo = self.get_image(favicon_url)

                return canny_logo
            else:
                logger.info("4-8) 크롤링 재시도 중..")
                driver.get(url=url)
                img = driver.find_element(
                    "xpath",
                    '//img[contains(@class, "h-16") and contains(@class, "w-16") and contains(@class, "object-cover")]'
                )
                img_url = img.get_attribute("src")
                if img_url:
                    logger.info(f"4-9) 팀 이미지 확인. URL: {img_url}")
                    canny_logo = self.get_image(img_url)
                    
                    logger.info("4-10) 로고 생성 완료")
                    return canny_logo
                

        except Exception as e:
            logger.info("4-10) 팀 파비콘 없음.")
            # print("❌ 이미지 추출 실패:", e)

            # try:
                # 정확한 클래스들이 모두 포함된 img 요소를 찾음
                # logger.info("4-8) 크롤링 재시도 중..")
                # img = driver.find_element(
                #     "xpath",
                #     '//img[contains(@class, "h-16") and contains(@class, "w-16") and contains(@class, "object-cover")]'
                # )
                # img_url = img.get_attribute("src")
                # if img_url:
                #     logger.info(f"4-9) 팀 이미지 확인. URL: {img_url}")
                #     canny_logo = self.get_image(img_url)
                    
                #     logger.info("4-10) 로고 생성 완료")
                #     return canny_logo

            # except Exception as e:
            #     logger.error("4-10) 팀 로고 불러오기 실패")
        

        finally:
            driver.quit()
    # def get_disquiet_exact_team_image(self, team_title: str):
    #     logger.info("4-4) 각 팀의 로고 찾는 중...")
    #     url = f"https://disquiet.io/product/{team_title}"
    #     page_url = self.data.deploymentUrl 

    #     # 1. 크롬 옵션 구성
    #     options = Options()
    #     options.binary_location = "/usr/bin/chromium-browser"
    #     options.add_argument("--headless")
    #     options.add_argument("--no-sandbox")
    #     options.add_argument("--disable-dev-shm-usage")
    #     options.add_argument("--disable-gpu")
    #     options.add_argument("--single-process")
    #     options.add_argument("--disable-software-rasterizer")
    #     options.add_argument("--remote-debugging-port=9222")

    #     # 2. 안전한 임시 유저 데이터 디렉토리
    #     with tempfile.TemporaryDirectory() as user_data_dir:
    #         options.add_argument(f'--user-data-dir={user_data_dir}')

    #         options.binary_location = "/opt/homebrew/bin/chromium"
    #         service = Service("/opt/homebrew/bin/chromedriver")
    #         # 3. chromedriver 직접 명시
    #         service = Service("/usr/bin/chromedriver")

    #         # 4. 버전 로그 확인
    #         try:
    #             chrome_ver = subprocess.check_output(["/usr/bin/chromium-browser", "--version"]).decode().strip()
    #             driver_ver = subprocess.check_output(["/usr/bin/chromedriver", "--version"]).decode().strip()
    #             logger.info(f"🔧 Chromium 버전: {chrome_ver}")
    #             logger.info(f"🔧 Chromedriver 버전: {driver_ver}")
    #         except Exception as e:
    #             logger.warning(f"버전 확인 실패: {e}")

    #         # 5. 드라이버 실행
    #         logger.info("4-5) 크롬 드라이버 실행")
    #         driver = webdriver.Chrome(service=service, options=options)

    #         try:
    #             driver.get(page_url)
    #             logger.info("4-6) 크롬 접속 성공")
    #             time.sleep(3)

    #             resp = requests.get(page_url)
    #             soup = BeautifulSoup(resp.text, "html.parser")

    #             icon_link = soup.find("link", rel=lambda x: x and "icon" in x)
    #             if icon_link and icon_link.get("href"):
    #                 logger.info("4-7) 팀 파비콘 있음.")
    #                 favicon_url = urljoin(page_url, icon_link["href"])
    #                 return self.get_image(favicon_url)

    #             else:
    #                 logger.info("4-8) 크롤링 재시도 중..")
    #                 driver.get(url=url)
    #                 img = driver.find_element(
    #                     "xpath",
    #                     '//img[contains(@class, "h-16") and contains(@class, "w-16") and contains(@class, "object-cover")]'
    #                 )
    #                 img_url = img.get_attribute("src")
    #                 if img_url:
    #                     logger.info(f"4-9) 팀 이미지 확인. URL: {img_url}")
    #                     return self.get_image(img_url)

    #         except Exception as e:
    #             logger.warning(f"4-10) 로고 크롤링 실패: {e}")

    #         finally:
    #             driver.quit()

    def insert_logo_on_badge(self, max_half_size=165):
        """
        배경 뱃지 이미지의 중심에 로고를 비율에 맞춰 삽입합니다.
        - 삽입 가능한 최대 크기는 중심 기준 ±120 영역 (즉 240x240)
        - 로고 비율 유지, 흰색은 투명 처리

        Args:
            max_half_size (int): 중심 기준 최대 절반 크기 (기본: 120)
        """
        # 이미지 열기
        badge = Image.fromarray(self.generate_corrected_badge(self.data.teamNumber)).convert("L")
        logo = Image.fromarray(self.get_disquiet_exact_team_image(self.data.title)).convert("L")

        # 중심점 및 삽입 가능 영역 크기
        center = (badge.width // 2, badge.height // 2)
        max_width = max_height = max_half_size * 2  # 240 x 240

        # 로고 크기 비율 조정 (긴 쪽을 240에 맞춤)
        logo_ratio = logo.width / logo.height
        if logo.width > logo.height:
            new_width = max_width
            new_height = int(max_width / logo_ratio)
        else:
            new_height = max_height
            new_width = int(max_height * logo_ratio)

        logo_resized = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 삽입 좌표 계산 (중앙 정렬)
        top_left = (
            center[0] - new_width // 2,
            center[1] - new_height // 2
        )

        # 흰색 배경은 투명하게 처리할 마스크 생성
        logo_mask = logo_resized.point(lambda p: 255 if p < 128 else 0)

        # 배경에 로고 삽입
        badge.paste(logo_resized, top_left, logo_mask)
        logger.info("4-11) 뱃지 이미지 생성 완료.")
        cv_image_logo = np.array(badge.convert("L"))
        canny_badge = cv2.Canny(cv_image_logo, 50, 150)
        return canny_badge

    
    def modi_mapping(self, mod_tags):
        if mod_tags == "원본":
            return " "
        elif mod_tags == "몽환적인":
            return "Watercolor"
        elif mod_tags == "화려한":
            return "glittery style with sparkling particles"
        elif mod_tags == "80년대 개성적인":
            return "in vaporwave aesthetic"
        elif mod_tags == "십자수":
            return "embroidered patch style"
        elif mod_tags == "가죽":
            return "Leather Patch Style"
        elif mod_tags == "우드":
            return "Wood Burned Badge"
    

    def build_badge_prompt(self, mod_tags: str, team_number: int) -> str:
        if mod_tags == None:
            return f"""A circular badge with a bright gold center and pastel {self.color} full-surface gradient without any other color, soft baby color palette, rim lighting, halo, iridescent gold, clean and elegant design, gold number "{team_number}" at the bottom. Highlight the logo, number more clearly. No dark colors, no gray, no brown, no metallic shadows"""
        #f"A kawaii badge with {self.data.title} on the top(it can be Hangul), number {team_number} on bottom and colored character on the middle of the image. Watercolor. Pixiv, Modernist. point {self.color} color with gradation inside the badge, iridescent gold. rimlighting, halo"
        else:
            return f"""A circular badge with a bright gold center and pastel {self.color} full-surface gradient. {self.modi_mapping(mod_tags)}. soft baby color palette, rim lighting, halo, iridescent gold, clean and elegant design, gold number "{team_number}" at the bottom. Highlight the logo, number more clearly. No dark colors, no gray, no brown, no metallic shadows."""

    # 아래는 한국어 -> 영어로 변환.
    def translate_korean_to_english(self, korean_prompt: str) -> str:
        return GoogleTranslator(source='ko', target='en').translate(korean_prompt)


if __name__ == '__main__':
    from app.fast_api.schemas.badge_schemas import BadgeModifyRequest
    import matplotlib.pyplot as plt

    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))


    dummy_data = BadgeModifyRequest(
        modificationTags="몽환적인",
        projectSummary=BadgeRequest(
            title="품앗이",
            introduction="카카오테크 부트캠프를 위한 트래픽 품앗이 플랫폼",
            detailedDescription="품앗이(Pumati)는 카카오테크 부트캠프를 위한 트래픽 품앗이 플랫폼입니다.\n\n서로의 프로젝트를 사용해주는 선순환을 통해 성공적인 트래픽 시나리오를 만들어 함께 성장하는 것이 우리의 목표입니다.\n\n품앗이(Pumati)의 주요 기능이에요!\n- 프로젝트 홍보 게시판: 우리 팀의 프로젝트를 홍보하고, 다른 팀의 프로젝트도 사용해볼까?\n- 트래픽 품앗이 기능: 다른 팀의 프로젝트를 사용할수록 우리 팀의 홍보 게시글 순위가 상승!\n- 후기 작성: 서로의 프로젝트를 리뷰하며 함께 성장해요~\n- 출석 체크 기능: 출석만 하면 품앗이 포인트가 올라간다고?\n\n흩어진 파이널 프로젝트들의 정보를 매번 찾아보기 어렵고, 트래픽 하나하나가 소중한 카카오테크 부트캠프 교육생들에게\n\n디스콰이엇(disquiet)과 달리 '트래픽 품앗이'와 '크레딧' 개념을 활용하여 실시간으로 프로젝트 홍보 게시글의 순위가 변동된다는 차별점이 있고,\n\n외부인들이 프로젝트에 쉽게 접근할 수 있도록 돕고, 나아가 교육생들끼리 서로의 프로젝트를 방문하고 응원함으로써(품앗이) 모두의 성공적인 프로젝트 경험을 함께 만들어 가는 기능을 제공합니다.",
            deploymentUrl="https://tebutebu.com/",
            githubUrl="https://github.com/orgs/100-hours-a-week/teams/8/repositories",
            tags=["품앗이"],
            teamId=4,
            term=2,
            teamNumber=8
        )
    )

    Badge_test_instance = BadgePrompt(dummy_data.projectSummary)
    badge_canny = Badge_test_instance.insert_logo_on_badge()

    cv_image_logo = np.array(badge_canny)
    canny_badge = cv2.Canny(cv_image_logo, 50, 150)
    cv2.imwrite("logo_canny.png", canny_badge)


    # plt.imshow(badge_canny)
    # plt.show()

#터미널에서 실행시키기   
#PYTHONPATH=/Users/hbin/KTD/pumati-ai/8-pumati-ai \
#/Users/hbin/KTD/pumati-ai/8-pumati-ai/.venv/bin/python \
#/Users/hbin/KTD/pumati-ai/8-pumati-ai/app/context_construction/prompts/badge_prompt.py

# PYTHONPATH=/Users/hbin/KTD/pumati-ai/8-pumati-ai \
# /Users/hbin/KTD/pumati-ai/8-pumati-ai/.venv/bin/python \
# /Users/hbin/KTD/pumati-ai/8-pumati-ai/app/context_construction/prompts/badge_prompt.py
