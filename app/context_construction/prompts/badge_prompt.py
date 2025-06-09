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
#from webcolors import rgb_to_name, CSS3_HEX_TO_NAMES
import webcolors 

class BadgePrompt:
    def __init__(self, data: BadgeRequest):
        self.data = data
        self.color= None
    
    def generate_corrected_badge(self, service_name: str, number: int, image_size: int = 800):
        center = (image_size // 2, image_size // 2)
        outer_radius = 350
        mid_radius = 330
        inner_radius = 240
        arc_radius = 270

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
        def draw_top_arc(draw_obj, radius, keep_start=-210, keep_end=30, thickness=1):
            for angle in range(keep_start, keep_end):
                theta = math.radians(angle)
                x = center[0] + int(radius * math.cos(theta))
                y = center[1] + int(radius * math.sin(theta))
                draw_obj.ellipse((x - thickness, y - thickness, x + thickness, y + thickness), fill=0)

        draw_top_arc(draw, mid_radius)
        draw_top_arc(draw, inner_radius)

        def draw_lines_on_image(draw_obj, line_width=3):
            """
            이미지에 여러 쌍의 점을 선으로 연결합니다.

            Parameters:
            - image: PIL.Image 객체
            - point_pairs: [(x1, y1), (x2, y2)] 형태의 좌표쌍 리스트
            - line_color: 선 색상 (RGB 튜플)
            - line_width: 선 두께
            """
            point_pairs = [
                ((118, 570), (194, 525)),
                ((606, 521), (685, 565))
            ]

            for start, end in point_pairs:
                draw_obj.line([start, end], width=line_width)


        # 함수 호출
        draw_lines_on_image(draw, line_width=3)


        # 4. 좌우 아치형 곡선
        def draw_arc(draw_obj, radius, start_angle, end_angle, thickness=4):
            for angle in range(start_angle, end_angle):
                theta = math.radians(angle)
                x = center[0] + int(radius * math.cos(theta))
                y = center[1] + int(radius * math.sin(theta))
                draw_obj.ellipse((x - thickness, y - thickness, x + thickness, y + thickness), fill=0)

        draw_arc(draw, arc_radius, -245, -225) #160, 270)       # 왼쪽 아치
        draw_arc(draw, arc_radius, 45, 65) #-90 % 360, 20)  # 오른쪽 아치

        # 5. 숫자 텍스트 삽입
        number_font = ImageFont.truetype("./app/utils/Pretendard-ExtraBold.ttf", 100)
        number_text = str(number)
        bbox = draw.textbbox((0, 0), number_text, font=number_font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((center[0] - text_width // 2, center[1] + outer_radius - 130), number_text, fill=0, font=number_font)

        #6. 서비스명 아치형 회전 텍스트
        def draw_rotated_text(draw_center, text, radius, total_angle=90, start_angle=-90):
            chars = list(text)

            if len(chars) -1 < 6:
                total_angle = 60

            elif len(chars) -1 < 9:
                total_angle = 90

            elif len(chars) -1 < 12:
                total_angle = 120

            elif len(chars) -1 < 15:
                total_angle = 150

            else:
                total_angle = 180

            font = ImageFont.truetype("./app/utils/Pretendard-ExtraLight.ttf", 55)
            angle_step = total_angle / (len(chars) - 1) if len(chars) > 1 else 0
            base_angle = start_angle - total_angle / 2

            for i, ch in enumerate(chars):
                angle_deg = base_angle + i * angle_step
                angle_rad = math.radians(angle_deg)
                x = draw_center[0] + int(radius * math.cos(angle_rad))
                y = draw_center[1] + int(radius * math.sin(angle_rad))

                dx = abs(draw_center[0] - x)
                dy = abs(draw_center[1] - y)
                base_rotation = np.rad2deg(np.arctan2(dx, dy))
                #print("dx", dx, "dy", dy, "arctan2", base_rotation)

                if i < len(text) // 2:
                    rotation = base_rotation
                else:
                # 전체 90도 시계 반대 회전
                    rotation = - base_rotation

                # char_img = Image.new("L", (65, 65), 255)
                # char_draw = ImageDraw.Draw(char_img)
                # # bbox = char_draw.textbbox((x, y), ch, font=font, anchor="mm")
                # # char_draw.rectangle(bbox, outline="red")
                # char_draw.text((25, 25), ch, font=font, fill=0, anchor="mm")
                # rotated_char = char_img.rotate(rotation, center=(25, 25), resample=Image.Resampling.BICUBIC, expand=False)
                # rotated_char_rgba = rotated_char.convert("RGBA")
                # #rotated_char = char_img.rotate(rotation, center=(25, 25), resample=Image.Resampling.BICUBIC)
                # base.paste(rotated_char_rgba, (x - 25, y - 25), rotated_char_rgba)
                char_img = Image.new("RGBA", (65, 65), (255, 255, 255, 0))  # 완전 투명 배경
                char_draw = ImageDraw.Draw(char_img)
                char_draw.text((25, 25), ch, font=font, fill=(0, 0, 0, 255), anchor="mm")

                rotated_char = char_img.rotate(rotation, center=(25, 25), resample=Image.Resampling.BICUBIC)
                base.paste(rotated_char, (x - 25, y - 25), rotated_char)

        draw_rotated_text(center, service_name, radius=280)

        # 7. Canny 엣지 적용 및 저장
        cv_image = np.array(base)
        #cv_image = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2GRAY)
        # plt.imshow(cv_image)
        # plt.show()
        canny_image = cv2.Canny(cv_image, 30, 100)
        print("created badge background")
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


    def get_disquiet_exact_team_image(self, team_title: str):
        url = f"https://disquiet.io/product/{team_title}"
        page_url = self.data.deploymentUrl #f"https://youtil.co.kr/"

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(3)  # JS 렌더링 대기

        try:
            resp = requests.get(page_url)
            soup = BeautifulSoup(resp.text, "html.parser")

            # 1. <link rel="icon"> 또는 <link rel="shortcut icon">
            icon_link = soup.find("link", rel=lambda x: x and "icon" in x)
            if icon_link and icon_link.get("href"):
                #print(urljoin(page_url, icon_link["href"]))
                ################# 공통부분 묶기
                response = requests.get(img_url)
                img = Image.open(BytesIO(response.content)).convert("RGB")

                small_img = img.resize((64, 64))  # 너무 작게는 하지 말기

                # 색상 목록 추출 (flatten)
                pixels = list(small_img.getdata())

                # 가장 많이 쓰인 색 찾기
                color_counts = Counter(pixels)
                most_common_colors = color_counts.most_common(5)
                css3_colors = self.load_css3_colors("./app/utils/css3_colors.json")
                color_names = [self.closest_css3_color_name(rgb, css3_colors) for rgb, _ in most_common_colors]
                # 색상명 리스트 추출
                print(color_names)  # 예: ['red', 'lime', 'blue']
                self.color = ', '.join(color_names)

                cv_image_logo = np.array(img)
                canny_logo = cv2.Canny(cv_image_logo, 50, 150)
                #####################
                return canny_logo

        except Exception as e:
            print("❌ 이미지 추출 실패:", e)

        try:
            # 정확한 클래스들이 모두 포함된 img 요소를 찾음
            img = driver.find_element(
                "xpath",
                '//img[contains(@class, "h-16") and contains(@class, "w-16") and contains(@class, "object-cover")]'
            )
            img_url = img.get_attribute("src")
            print("✅ 정확한 위치의 이미지 URL:", img_url)
            response = requests.get(img_url)
            img = Image.open(BytesIO(response.content)).convert("RGB")

            small_img = img.resize((64, 64))  # 너무 작게는 하지 말기

            # 색상 목록 추출 (flatten)
            pixels = list(small_img.getdata())

            # 가장 많이 쓰인 색 찾기
            color_counts = Counter(pixels)
            most_common_colors = color_counts.most_common(5)
            css3_colors = self.load_css3_colors("./app/utils/css3_colors.json")
            color_names = [self.closest_css3_color_name(rgb, css3_colors) for rgb, _ in most_common_colors]
            # 색상명 리스트 추출
            print(color_names)  # 예: ['red', 'lime', 'blue']
            self.color = ', '.join(color_names)

            cv_image_logo = np.array(img)
            canny_logo = cv2.Canny(cv_image_logo, 50, 150)
            print("created logo")
            return canny_logo

        except Exception as e:
            print("❌ 이미지 추출 실패:", e)
        

        finally:
            driver.quit()

    def insert_logo_on_badge(self, max_half_size=165):
        """
        배경 뱃지 이미지의 중심에 로고를 비율에 맞춰 삽입합니다.
        - 삽입 가능한 최대 크기는 중심 기준 ±120 영역 (즉 240x240)
        - 로고 비율 유지, 흰색은 투명 처리

        Args:
            max_half_size (int): 중심 기준 최대 절반 크기 (기본: 120)
        """
        # 이미지 열기
        badge = Image.fromarray(self.generate_corrected_badge(self.data.title, self.data.teamNumber)).convert("L")#Image.open(badge_path).convert("L")
        logo = Image.fromarray(self.get_disquiet_exact_team_image(self.data.title)).convert("L")#Image.open(logo_path).convert("L")   

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
        print("created badge")
        cv_image_logo = np.array(badge.convert("L"))
        canny_badge = cv2.Canny(cv_image_logo, 50, 150)
        return canny_badge

    def build_badge_prompt(self, mod_tags: List[str], team_number: int) -> str:
        if mod_tags == None:
            return f"A kawaii badge with {self.data.title} on the top(it can be Hangul), number {team_number} on bottom and colored character on the middle of the image. Watercolor. Pixiv, Modernist. point {self.color} color with gradation inside the badge, iridescent gold. rimlighting, halo"
        else:
            return f"A kawaii badge with {self.data.title} on the top(it can be Hangul), number {team_number} on bottom and colored character on the middle of the image. Watercolor. Pixiv, Modernist. point {self.color} color with gradation inside the badge, iridescent gold. rimlighting, halo. more {','.join(mod_tags)}"

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
        modificationTags=["귀엽게", "예쁘게"],
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


    plt.imshow(badge_canny)
    plt.show()

#터미널에서 실행시키기   
#PYTHONPATH=/Users/hbin/KTD/pumati-ai/8-pumati-ai \
#/Users/hbin/KTD/pumati-ai/8-pumati-ai/.venv/bin/python \
#/Users/hbin/KTD/pumati-ai/8-pumati-ai/app/context_construction/prompts/badge_prompt.py
