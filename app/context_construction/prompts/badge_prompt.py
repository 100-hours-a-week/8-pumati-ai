#badge_prompt.py

from app.fast_api.schemas.badge_schemas import BadgeRequest  

from deep_translator import GoogleTranslator
#from typing import List
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFilter, ImageEnhance, ImageFont #새로 추가됨.
import math, json
import cv2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
import requests, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import BytesIO
from collections import Counter
from urllib.parse import quote

import logging, os, tempfile,cairosvg #subprocess, stat

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class BadgePrompt:
    def __init__(self, data: BadgeRequest):
        self.data = data
        self.color= None
        self.scene_color = None
    
    async def generate_corrected_badge(self, number: int, image_size: int = 800):
        center = (image_size // 2, image_size // 2)
        outer_radius = 350

        # 1. 흰 배경 생성
        base = Image.new("L", (image_size, image_size), 255)
        draw = ImageDraw.Draw(base)

        draw.ellipse([
            center[0] - outer_radius, center[1] - outer_radius,
            center[0] - outer_radius, center[1] - outer_radius
        ], outline=0, width=6)

        # 5. Canny 엣지 적용 및 저장
        cv_image = np.array(base)
        canny_image = cv2.Canny(cv_image, 30, 100)
        logger.info("3-3) Canny이미지 배경 생성 완료")
        return canny_image


    async def load_css3_colors(self, path="css3_colors.json"):
        with open(path, "r") as f:
            return json.load(f)

    async def closest_css3_color_name(self, rgb, css3_colors):
        min_dist = float('inf')
        closest_name = None

        for name, value in css3_colors.items():
            # value는 [R, G, B]
            dist = sum((c1 - c2) ** 2 for c1, c2 in zip(rgb, value))
            if dist < min_dist:
                min_dist = dist
                closest_name = name

        return closest_name
    
    async def get_image(self, url):
        response = requests.get(url)
        content_type = response.headers.get("Content-Type", "")

        if "svg" in content_type or url.lower().endswith(".svg"):
            # SVG는 cairosvg로 처리
            png_data = cairosvg.svg2png(bytestring=response.content)
            img = Image.open(BytesIO(png_data)).convert("RGB")
        else:
            # 일반 이미지 처리
            img = Image.open(BytesIO(response.content)).convert("RGB")

        small_img = img.resize((64, 64))  # 너무 작게는 하지 말기

        # 색상 목록 추출 (flatten)
        pixels = list(small_img.getdata())

        # 가장 많이 쓰인 색 찾기
        color_counts = Counter(pixels)
        most_common_colors = color_counts.most_common(3) #or ["white"]

        logger.info(f"3-7-1) 팀 로고 색을 추출합니다.")

        if not most_common_colors:
            # 흰색(RGB)과 가상의 count 값으로 대체
            most_common_colors = [((255, 255, 255), 9999)]

        css3_colors = await self.load_css3_colors("./app/utils/css3_colors.json")
        color_names = [await self.closest_css3_color_name(rgb, css3_colors) for rgb, _ in most_common_colors][:4]
        self.color = ', '.join(color_names)

        css3_BPB_colors = await self.load_css3_colors("./app/utils/css3_blue_purple_black_colors_rgb.json")
        BPB_color_names = [await self.closest_css3_color_name(rgb, css3_BPB_colors) for rgb, _ in most_common_colors][:4]
        # 색상명 리스트 추출  # 예: ['red', 'lime', 'blue']
        self.scene_color = ', '.join(BPB_color_names)

        logger.info(f"3-7-2) 색 추출 완료. all colors: {self.color}, Blue, purple, black colors: {self.scene_color}")
        
        #해상도 높이기 
        logger.info(f"3-7-3) 이미지의 해상도를 높입니다.")
        
        np_img = np.array(img) #np에서 512x512로 확장
        #upscaled = cv2.resize(np_img, (256, 256), interpolation=cv2.INTER_LANCZOS4)
        logger.info(f"3-7-4) PIL에서 명암 강화")
        #pil_img = Image.fromarray(upscaled) #PIL에서 명암 강화
        #blurred = pil_img.filter(ImageFilter.GaussianBlur(radius=1.2))
        #contrast = ImageEnhance.Contrast(pil_img).enhance(1.5)   # 대비 ↑
        #sharp = ImageEnhance.Sharpness(contrast).enhance(2.0)
        logger.info(f"3-7-5) np에서 canny이미지 획득")
        cv_image_logo = np.array(np_img) #np에서 canny이미지 획득
        canny_logo = cv2.Canny(cv_image_logo, 50, 150) #50, 150)
        return canny_logo

    async def find_logo_image_url(soup, page_url):
        # 1. alt에 'logo'가 포함된 이미지 찾기
        img_tag = soup.find("img", alt=lambda x: x and "logo" in x.lower())
        if img_tag and img_tag.get("src"):
            return urljoin(page_url, img_tag["src"])

        # 2. src에 'logo'가 포함된 이미지 찾기
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if "logo" in src.lower():
                return urljoin(page_url, src)

        # 3. class에 'logo'가 포함된 이미지 찾기
        for img in soup.find_all("img"):
            classes = img.get("class", [])
            if any("logo" in cls.lower() for cls in classes):
                src = img.get("src")
                if src:
                    return urljoin(page_url, src)

        return None 
    
    async def get_disquiet_exact_team_image(self, team_title: str):
        logger.info("3-4) 각 팀의 로고를 크롤링...")
        encoded_title = quote(team_title.lower())
        url = f"https://disquiet.io/product/{encoded_title}"
        page_url = self.data.deploymentUrl

        options = Options()
        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--no-zygote')

        logger.info("3-5) 크롬 트라이버 생성중...")
        with tempfile.TemporaryDirectory() as user_data_dir:
            try:
                try:
                    options.add_argument(f'--user-data-dir={user_data_dir}')
                    service = Service("/usr/bin/chromedriver")
                    driver = webdriver.Chrome(service=service, options=options)

                    driver.get(page_url)
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'link[rel*="icon"]'))
                    )
                    #time.sleep(2)  # JS 렌더링 대기
                    logger.info("3-6) 크롤링 준비 완료")
                except:
                    logger.info("3-6) 크롤링 불가")

                # 정적 페이지 파비콘 크롤링
                try:
                    logger.info("3-7) 정적 크롤링 시작")
                    
                    favicon_url = urljoin(page_url, "favicon.ico")
                    logger.info(f"3-7-1){favicon_url}에 파비콘을 요청합니다.")
                    resp = requests.get(favicon_url, timeout=3, allow_redirects=True)
                    if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("image"):
                        logger.info("3-7-2) 파비콘 ico 있음.")
                        canny_logo = await self.get_image(favicon_url)
                        return canny_logo
                except Exception as e:
                    logger.info(f"3-7-e) 파비콘 ico 없음: {e}")
                
                # 동적 페이지 파비콘 크롤링
                try:
                    logger.info(f"3-8) 웹페이지 동적 크롤링 시작")
                    html = driver.page_source
                    current_url = driver.current_url
                    #resp = requests.get(page_url, timeout=3)
                    logger.info(f"3-8-1) {current_url}에서 파비콘 주소를 찾습니다.")
                    soup = BeautifulSoup(html, "html.parser")
                    logger.info(f"3-8-2) {soup}")
                    # 1. <link rel="icon"> 또는 <link rel="shortcut icon">
                    icon_link = soup.find("link", rel=lambda x: x and "icon" in x)
                    logger.info(f"3-8-3) {icon_link}를 찾았으며, {icon_link.get('href')}입니다.")
                    if icon_link and icon_link.get("href"):
                        logger.info("3-8-4) 팀 파비콘 있음.")
                        favicon_url = urljoin(current_url, icon_link["href"])
                        canny_logo = await self.get_image(favicon_url)
                        return canny_logo
                except Exception as e:
                    logger.info(f"3-8-e) 파비콘 ico 없음: {e}")
                
                #디스콰이엇 크롤링
                try:
                    logger.info("3-9) 디스콰이엇에서 팀 이미지를 크롤링 해 옵니다.")
                    driver.get(url=url)
                    #페이지가 켜질 때 까지 3초 기다림.
                    img = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((
                            By.XPATH, '//img[contains(@class, "h-24") and contains(@class, "w-24") and contains(@class, "object-cover")]'
                        ))
                    )
                    logger.info(f"3-9-1) 이미지: {img}")
                    img_url = img.get_attribute("src")
                    logger.info(f"3-9-2) 팀 이미지 URL: {img_url}")
                    canny_logo = await self.get_image(img_url)
                    return canny_logo
                except Exception as e:
                    logger.error(f"3-9-e) 이미지 못 찾음: {repr(e)}")

                #로고 크롤링
                try:
                    logger.error(f"3-10) favicon이 없어, logo를 크롤링 합니다.")
                    driver.get(page_url)
                    logger.error(f"3-10-1) JS 랜더링을 기다립니다.")
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'link[rel*="icon"]'))
                    )
                    current_url = driver.current_url
                    html = driver.page_source
                    soup = BeautifulSoup(html, "html.parser")
                    logo_url = await self.find_logo_image_url(soup, current_url)
                    logger.info(f"3-10-2) 팀 로고 URL: {logo_url}")
                except Exception as e:
                    logger.error(f"3-10-e) 파비콘 못 찾음: {repr(e)}")



            except Exception as e:
                logger.info("3-e) 팀 파비콘 없음.")
        
            finally:
                driver.quit()

    async def create_letter_logo_canny(team_title: str, image_size: int = 490):
        # 1. 흰 배경 이미지 생성
        try:
            logger.error(f"3-11-1) 배경 생성")
            image = Image.new("RGB", (image_size, image_size), color="white")
            draw = ImageDraw.Draw(image)

            # 2. 글자 설정
            logger.error(f"3-11-2) 글자 생성")
            letter = team_title.strip()[0].upper()  # 첫 글자 (공백 제거 + 대문자)
            
            try:
                logger.error(f"3-11-3) 폰트 설정")
                font = ImageFont.truetype("/app/utils/Pretendard-Black.ttf", int(image_size * 0.6))  # 시스템에 있는 TTF 폰트
            except:
                font = ImageFont.load_default()

            text_size = draw.textbbox((0, 0), letter, font=font)
            text_w = text_size[2] - text_size[0]
            text_h = text_size[3] - text_size[1]
            text_x = (image_size - text_w) // 2
            text_y = (image_size - text_h) // 2

            # 3. 글자 그림
            logger.error(f"3-11-4) 글자 삽입")
            draw.text((text_x, text_y), letter, fill="black", font=font)

            # 4. PIL → NumPy로 변환
            np_img = np.array(image)

            # 5. OpenCV: 그레이 + Canny
            logger.error(f"3-11-5) canny이미지 생성")
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, threshold1=100, threshold2=200)

            # 6. 엣지 이미지 → Pillow 이미지로 복원 (mode="L")
            logger.error(f"3-11-6) 로고 생성 완료")
            canny_image = Image.fromarray(edges)

            return canny_image
        except Exception as e:
            logger.info(f"3-11-e) 로고 생성 불가. : {e}")



    async def insert_logo_on_badge(self, max_half_size=245):
        """
        배경 뱃지 이미지의 중심에 로고를 비율에 맞춰 삽입합니다.
        - 삽입 가능한 최대 크기는 중심 기준 ±120 영역 (즉 240x240)
        - 로고 비율 유지, 흰색은 투명 처리

        Args:
            max_half_size (int): 중심 기준 최대 절반 크기 (기본: 120)
        """
        # 이미지 열기
        badge = Image.fromarray(await self.generate_corrected_badge(self.data.teamNumber)).convert("L")
        #logo = Image.fromarray(await self.get_disquiet_exact_team_image(self.data.title)).convert("L")
        logo_array = await self.get_disquiet_exact_team_image(self.data.title)

        if logo_array is None:
            logger.error(f"3-11) logo가 None이므로 로고를 생성합니다.")
            logo = await self.create_letter_logo_canny(self.data.title)  # PIL.Image
            self.color = "blue"
            self.scene_color = "blue"
        else:
            logo = Image.fromarray(logo_array).convert("L")  # NumPy → PIL.Image



        logger.info("4-1) 로고 병합중...")
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

        #logo_resized = logo.resize((1024, 1024), Image.Resampling.LANCZOS)
        logo_resized = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 삽입 좌표 계산 (중앙 정렬)
        top_left = (
            center[0] - new_width // 2,
            center[1] - new_height // 2
        )

        logo_gray = logo_resized.convert("L")
        logo_mask = ImageOps.invert(logo_gray).filter(ImageFilter.GaussianBlur(2))

        # 배경에 로고 삽입
        badge.paste(logo_resized, top_left, logo_mask)
        logger.info("4-2) 뱃지 이미지 생성 완료.")
        cv_image_logo = cv2.resize(np.array(badge.convert("L")), (512, 512))
        logger.info("4-3) 이미지 해상도: 512 x 512")
        canny_badge = cv2.Canny(cv_image_logo, 50, 150)
        return canny_badge
    

    def build_badge_prompt(self, mod_tags: str, team_number: int) -> str:
        if mod_tags == "뉴스":
            return f"NewspaperWorld, high resolution, beat quality, Masterpiece, detailed, captivating, Magnification. Simple soft Logo Icon, white background, Sunlight, Soft natural light"
        elif mod_tags == "자연 풍경": # 45개의 (파랑, 보랑, 검정 계열 색상을 입력으로 넣음.)
            return f"hyrule, scenery, outdoors, no humans. high resolution, beat quality, Masterpiece, detailed, captivating, Magnification. Simple soft {self.scene_color} Logo Icon, white background, Sunlight, Soft natural light"
        elif mod_tags == "우드":
            return f"woodcarvingcd, logo. high resolution, beat quality, Masterpiece, detailed, captivating, Magnification. Simple soft Logo Icon, white background."
        elif mod_tags == "픽셀":
            return f"pixel world. beat quality, Masterpiece, detailed, captivating, Magnification.  Simple soft {self.color} Logo Icon, white background, Sunlight, Soft natural light"
        elif mod_tags == "게임":
            return f"lol_splash, League of Legends Splash Art, dynamic, lolstyle, high resolution, clean lines, beat quality, Masterpiece, detailed, captivating, Magnification. Simple soft {self.color} Logo Icon, white background, Sunlight, Soft natural light"
        else:
            return f"badge, logo. high resolution, clean lines, vector style, beat quality, Masterpiece, detailed, captivating, Magnification. Simple soft {self.color} Logo Icon, white background, Sunlight, Soft natural light"


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
