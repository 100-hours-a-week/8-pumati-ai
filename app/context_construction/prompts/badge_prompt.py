#badge_prompt.py

from app.fast_api.schemas.badge_schemas import BadgeRequest  

#from deep_translator import GoogleTranslator
#from typing import List
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFilter, ImageFont #새로 추가됨. ImageEnhance,
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
import onnxruntime as ort

import logging, os, tempfile,cairosvg, gc, wordninja #subprocess, stat

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
            center[0] + outer_radius, center[1] + outer_radius
        ], outline=0, width=6)

        # 5. Canny 엣지 적용 및 저장
        cv_image = np.array(base)
        canny_image = cv2.Canny(cv_image, 100, 200)
        logger.info("3-3) Canny이미지 배경 생성 완료")
        
        del base, draw, cv_image
        gc.collect()

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
    
    async def upscale_with_onnx(self, image: np.ndarray, model_path: str = "realesrgan-x2.onnx") -> np.ndarray:
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img_rgb = np.transpose(img_rgb, (2, 0, 1))[np.newaxis, ...]  # shape: (1, 3, H, W)

        session = ort.InferenceSession(model_path)
        input_name = session.get_inputs()[0].name
        output = session.run(None, {input_name: img_rgb})[0]

        output_img = np.clip(output[0].transpose(1, 2, 0), 0, 1) * 255

        del img_rgb, session, input_name, output
        gc.collect()

        return output_img.astype(np.uint8)
    
    async def remove_alpha_to_white_bg(self, PIL_img: Image.Image, new_w, new_h) -> Image.Image:
        """
        이미지에 알파 채널이 있으면 흰 배경에 붙여서 RGB 이미지로 변환합니다.
        알파 채널이 없으면 그대로 반환합니다.
        """
        if PIL_img.mode != "RGBA":
            PIL_img = PIL_img.convert("RGBA")

        # 흰 배경 생성
        bg = Image.new("RGBA", (128,128), (255, 255, 255, 255))

        x_offset = (128 - new_w) // 2
        y_offset = (128 - new_h) // 2

        # 알파 마스크로 병합
        alpha = PIL_img.split()[3]
        bg.paste(PIL_img, (x_offset, y_offset), mask=alpha)
        # plt.imshow(bg) #삭제
        # plt.show()

        del PIL_img, alpha
        gc.collect()

        # RGB로 최종 변환
        return bg.convert("RGB")
    
    async def keep_ratio(self, pil_img): #np_img):
        #h, w = np_img.shape[:2]
        # w, h = pil_img.size

        # # 비율 유지
        # scale = 128 / max(h, w)
        # new_w = int(w * scale)
        # new_h = int(h * scale)

        # resized_logo = cv2.resize(np_img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

        w, h = pil_img.size

        # 위 아래 2픽셀씩 자르기 (좌측, 위, 우측, 아래)
        # cropped_img = pil_img.crop((5, 5, w - 5, h - 5))
        # w, h = cropped_img.size

        logger.info(f"img_size: {w}, {h}")
        # if w < 50 or h < 50:
        #     return None

        # 비율 유지하여 128 크기로 맞추기
        scale = 128 / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)

        line_location_w = (128 - new_w) // 2
        line_location_h = (128 - new_h) // 2
        #print("line_location_w", line_location_w, "line_location_h", line_location_h)

        # 이미지 리사이즈 (LANCZOS는 고품질)
        resized_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
        # plt.imshow(resized_img) #삭제
        # plt.show()
        
        background = await self.remove_alpha_to_white_bg(resized_img, new_w, new_h)
        # plt.imshow(background)
        # plt.show()

        # # 흰색 배경 128x128 생성
        # background = Image.new("RGB", (128, 128), (255, 255, 255, 255))
        # plt.imshow(background, cmap='gray') #삭제
        # plt.show()

        # # 중앙 배치 좌표 계산
        # x_offset = (128 - new_w) // 2
        # y_offset = (128 - new_h) // 2

        # # 배경에 붙이기
        # #background.paste(resized_img, (x_offset, y_offset))
        # background.paste(resized_img, mask=resized_img.split()[3])

        del resized_img 
        gc.collect()

        return background, line_location_w, line_location_h
        # background = Image.new("RGB", (128, 128), (255, 255, 255))
        # # 3채널짜리 128x128 배경 생성 (흰색)
        # background = np.zeros((128, 128, 3), dtype=np.uint8) * 255

        # # 중앙에 배치하기 위해 시작점 계산
        # y_offset = (128 - new_h) // 2
        # x_offset = (128 - new_w) // 2

        # # 배경 위에 얹기
        # background[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized_logo

        # del resized_logo
        # gc.collect()

        # return background

    async def img_preprocessing(self, Pil_image):
        small_img = Pil_image.resize((64, 64))  # 주요 색 추출을 위해 이미지 사이즈 조정.

        # 색상 목록 추출 (flatten)
        pixels = list(small_img.getdata())

        # 가장 많이 쓰인 색 찾기
        color_counts = Counter(pixels)
        most_common_colors = color_counts.most_common(3) #or ["white"]

        logger.info(f"3-7-4) 팀 로고 색을 추출합니다.")

        if not most_common_colors:
            # 흰색(RGB)과 가상의 count 값으로 대체
            most_common_colors = [((255, 255, 255), 9999)]

        css3_colors = await self.load_css3_colors("./app/utils/css3_colors.json")
        color_names = [await self.closest_css3_color_name(rgb, css3_colors) for rgb, _ in most_common_colors][:4]
        # if "black" in color_names:
        #     color_names.remove("black")

        self.color = ', '.join(color_names)

        css3_BPB_colors = await self.load_css3_colors("./app/utils/css3_blue_purple_black_colors_rgb.json")
        BPB_color_names = [await self.closest_css3_color_name(rgb, css3_BPB_colors) for rgb, _ in most_common_colors][:4]
        # 색상명 리스트 추출  # 예: ['red', 'lime', 'blue']
        self.scene_color = ', '.join(BPB_color_names)

        logger.info(f"3-7-5) 색 추출 완료. all colors: {self.color}, Blue, purple, black colors: {self.scene_color}")
        
        #해상도 높이기 
        logger.info(f"3-7-6) 이미지의 해상도를 높입니다.")
        
        #np_img = np.array(img) #np에서 512x512로 확장
        logger.info(f"3-7-7) 128x128로 보간.")
        input_logo_resized, line_location_w, line_location_h = await self.keep_ratio(Pil_image)
        logger.info(f"3-7-8) upscailing모델을 사용합니다.")
        input_logo_resized = np.array(input_logo_resized)

        upscaled = await self.upscale_with_onnx(input_logo_resized, "./app/utils/realesrgan-general-x4v3.onnx")
        logger.info(f"3-7-9) 업스케일링 완료")
        resized = cv2.resize(upscaled, (512, 512), interpolation=cv2.INTER_LANCZOS4)
        canny_logo = cv2.Canny(resized, 50, 200)

        #print("line_location_w", line_location_w, "line_location_h", line_location_h)

        if line_location_w > 0.5 :
            # canny_logo[line_location_w * 4 - 3 : line_location_w * 4 + 3, :] = 0
            # canny_logo[511 - line_location_w * 4 - 3 : 511 - line_location_w * 4 + 3, :] = 0
            canny_logo[:, line_location_w * 4 - 5 : line_location_w * 4 + 5] = 0
            canny_logo[:, 511 - (line_location_w * 4) - 5 : 511 - (line_location_w * 4) + 5] = 0

        if line_location_h > 0.5 :
            canny_logo[line_location_h * 4 - 5 : line_location_h * 4 + 5, :] = 0
            canny_logo[511 - line_location_h * 4 - 5 : 511 - line_location_h * 4 + 5, :] = 0
        
        #선을 두껍게 변경.s
        kernel = np.ones((3, 3), np.uint8)  # 커널 크기 (선 굵기 조절)
        dilated_logo = cv2.dilate(canny_logo, kernel, iterations=2)  # 반복 횟수도 조절 가능


        del Pil_image, small_img, pixels, input_logo_resized, upscaled, resized, canny_logo

        return dilated_logo

    
    async def get_image(self, url):
        response = requests.get(url)
        content_type = response.headers.get("Content-Type", "")

        if "svg" in content_type or url.lower().endswith(".svg"):
            # SVG는 cairosvg로 처리
            logger.info(f"3-7-1) 팀 로고 색을 추출합니다.")
            png_data = cairosvg.svg2png(bytestring=response.content)
            img = Image.open(BytesIO(png_data)).convert("RGB")
            w, h = img.size
            logger.info(f"3-7-2) {w}, {h}")
            if w < 50 or h < 50:
                logger.info(f"3-7-3) 이미지를 rescailing합니다.")
                #이후 w < 50 or h < 50인 경우는 pass하도록 설정되어 있음.
                scale = 52 / min(h, w) # 확장자가 svg인 경우, w,h중 작은 길이를 기준으로 52이상으로 upscailing하여 pass하지 않도록 함.
                img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        else:
            # 일반 이미지 처리
            img = Image.open(BytesIO(response.content)).convert("RGB")

        dilated_logo = await self.img_preprocessing(img)

        del response, img
        gc.collect()

        return dilated_logo

    async def find_logo_image_url(self, soup, page_url):
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
    
    def slugify_team_name(self, name: str) -> str:
        # 영어로만 이루어진 경우에만 분리
        if name.isascii() and name.isalpha():
            words = wordninja.split(name)
            return "-".join(words).lower()
        else:
            return name  # 한글이거나 혼합된 경우 그대로 반환
    
    async def get_disquiet_exact_team_image(self, team_title: str):
        logger.info("3-4) 각 팀의 로고를 크롤링...")
        page_url = self.data.deploymentUrl

        if self.data.teamNumber == 20:
            logger.info("3-4-1) 20팀 이미지를 불러옵니다")
            img_20 = Image.open("./app/utils/20.ico")
            return await self.img_preprocessing(img_20)


        elif self.data.teamNumber == 14:
            logger.info("3-4-1) 14팀 이미지를 불러옵니다.")
            img_14 = Image.open("./app/utils/14.png")
            return await self.img_preprocessing(img_14)
        
        elif self.data.teamNumber == 3:
            logger.info("3-4-1) 3팀 이미지를 불러옵니다.")
            img_3 = Image.open("./app/utils/3.png")
            return await self.img_preprocessing(img_3) #await self.get_image("https://www.meowng.com/logo.svg")


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
                    #logger.info(f"3-8-2) {soup}")
                    # 1. <link rel="icon"> 또는 <link rel="shortcut icon">
                    icon_link = soup.find("link", rel=lambda x: x and "icon" in x)
                    logger.info(f"3-8-2) {icon_link}를 찾았으며, {icon_link.get('href')}입니다.")
                    if icon_link and icon_link.get("href"):
                        logger.info("3-8-3) 팀 파비콘 있음.")
                        favicon_url = urljoin(current_url, icon_link["href"])
                        canny_logo = await self.get_image(favicon_url)
                        return canny_logo
                except Exception as e:
                    logger.info(f"3-8-e) 파비콘 ico 없음: {e}")
                
                #디스콰이엇 크롤링
                try:
                    logger.info("3-9) 디스콰이엇에서 팀 이미지를 크롤링 해 옵니다.")
                    #encoded_title = quote(team_title.lower())
                    encoded_title = quote(self.slugify_team_name(team_title.lower()))
                    url = f"https://disquiet.io/product/{encoded_title}"
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
                    canny_logo = await self.get_image(logo_url)
                    return canny_logo
                except Exception as e:
                    logger.error(f"3-10-e) 파비콘 못 찾음: {repr(e)}")



            except Exception as e:
                logger.info("3-e) 팀 파비콘 없음.")
        
            finally:
                driver.quit()
                gc.collect()

    async def create_letter_logo_canny(self, team_title: str, image_size: int = 490):
        # 1. 흰 배경 이미지 생성
        try:
            logger.error(f"3-11-1) 배경 생성")
            image_size = int(image_size)
            image = Image.new("RGB", (image_size, image_size), color="white")
            draw = ImageDraw.Draw(image)

            # 2. 글자 설정
            logger.error(f"3-11-2) 글자 생성")
            letter = team_title.strip()[0].upper()  # 첫 글자 (공백 제거 + 대문자)
            
            try:
                logger.error(f"3-11-3) 폰트 설정")
                font = ImageFont.truetype("./app/utils/Pretendard-Black.ttf", int(image_size * 0.6))  # 시스템에 있는 TTF 폰트
            except:
                font = ImageFont.load_default()

            text_size = draw.textbbox((0, 0), letter, font=font)
            text_w = text_size[2] - text_size[0]
            text_h = text_size[3] - text_size[1]
            text_x = (image_size - text_w) // 2
            text_y = (image_size - text_h) // 2
            logger.info(f"text_w, text_h : {text_w}, {text_h} / text_x, text_y : {text_x}, {text_y}")

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

            del image, draw, np_img, gray, edges
            gc.collect()

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
            logo = await self.create_letter_logo_canny(team_title = self.data.title)  # PIL.Image
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
        canny_badge = cv2.Canny(cv_image_logo, 100, 200)
        # plt.imshow(canny_badge)
        # plt.show()

        del badge, logo_array, logo, logo_resized, logo_gray, logo_mask, cv_image_logo
        gc.collect()

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
    import os, asyncio
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))


    dummy_data = BadgeModifyRequest(
        modificationTags=["뉴스"],
        projectSummary=BadgeRequest(
            title="품앗이",
            introduction="카카오테크 부트캠프를 위한 트래픽 품앗이 플랫폼",
            detailedDescription="품앗이(Pumati)는 카카오테크 부트캠프를 위한 트래픽 품앗이 플랫폼입니다.\n\n서로의 프로젝트를 사용해주는 선순환을 통해 성공적인 트래픽 시나리오를 만들어 함께 성장하는 것이 우리의 목표입니다.\n\n품앗이(Pumati)의 주요 기능이에요!\n- 프로젝트 홍보 게시판: 우리 팀의 프로젝트를 홍보하고, 다른 팀의 프로젝트도 사용해볼까?\n- 트래픽 품앗이 기능: 다른 팀의 프로젝트를 사용할수록 우리 팀의 홍보 게시글 순위가 상승!\n- 후기 작성: 서로의 프로젝트를 리뷰하며 함께 성장해요~\n- 출석 체크 기능: 출석만 하면 품앗이 포인트가 올라간다고?\n\n흩어진 파이널 프로젝트들의 정보를 매번 찾아보기 어렵고, 트래픽 하나하나가 소중한 카카오테크 부트캠프 교육생들에게\n\n디스콰이엇(disquiet)과 달리 '트래픽 품앗이'와 '크레딧' 개념을 활용하여 실시간으로 프로젝트 홍보 게시글의 순위가 변동된다는 차별점이 있고,\n\n외부인들이 프로젝트에 쉽게 접근할 수 있도록 돕고, 나아가 교육생들끼리 서로의 프로젝트를 방문하고 응원함으로써(품앗이) 모두의 성공적인 프로젝트 경험을 함께 만들어 가는 기능을 제공합니다.",
            deploymentUrl="https://tebutebu.com/",
            githubUrl="https://github.com/orgs/100-hours-a-week/teams/8/repositories",
            tags=["품앗이"],
            teamId=4,
            term=2,
            teamNumber=3
        )
    )

    Badge_test_instance = BadgePrompt(dummy_data.projectSummary)
    badge_canny = asyncio.run(Badge_test_instance.insert_logo_on_badge())

    cv_image_logo = np.array(badge_canny)
    canny_badge = cv2.Canny(cv_image_logo, 100, 200)
    
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
