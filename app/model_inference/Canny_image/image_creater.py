from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

def draw_centered_number_with_circle(
    number: str,
    font_path: str,
    size=(512, 512),
    font_size=300,
    circle_margin=20,
    stroke_width=2,
    save_path=None
):
    # 1. 이미지 생성 (흰 배경)
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)

    # 2. 원형 테두리 그리기
    left_up = (circle_margin, circle_margin)
    right_down = (size[0] - circle_margin, size[1] - circle_margin)
    draw.ellipse([left_up, right_down], outline="black", width=stroke_width)

    # 3. 폰트 설정
    font = ImageFont.truetype(font_path, font_size)

    # 4. 텍스트 위치 계산 (baseline 기준 정확한 중앙 정렬)
    bbox = draw.textbbox((0, 0), number, font=font, stroke_width=stroke_width)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_pos = ((size[0] - text_w) // 2 - bbox[0], (size[1] - text_h) // 2 - bbox[1])

    # 5. 숫자 텍스트 그리기 (white + black outline)
    draw.text(
        text_pos,
        number,
        font=font,
        fill="white",
        stroke_width=stroke_width,
        stroke_fill="black"
    )

    img_np = np.array(image.convert("L"))
    edges = cv2.Canny(img_np, 100, 200)
    edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

    # 6. 저장 또는 리턴
    if save_path:
        Image.fromarray(edges_rgb).save(save_path)
    return image

font_path = "/Users/hbin/KTD/pumati-ai/8-pumati-ai/app/model_inference/Canny_image/Lexend-Black.ttf"

for i in range(1, 23):
    print(i)
    if i <10:
        img = draw_centered_number_with_circle(
            number=f"{i}",
            font_path=font_path,
            save_path=f"/Users/hbin/KTD/pumati-ai/8-pumati-ai/app/model_inference/Canny_image/badge_{i}.png",
            font_size = 300
        )
    else:
        img = draw_centered_number_with_circle(
            number=f"{i}",
            font_path=font_path,
            save_path=f"/Users/hbin/KTD/pumati-ai/8-pumati-ai/app/model_inference/Canny_image/badge_{i}.png",
            font_size = 230
        )

# def generate_canny_badge(number: str, size=(512, 512)):
#     # 2. Canny 변환
#     img_np = np.array(image.convert("L"))
#     edges = cv2.Canny(img_np, 100, 200)
#     edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

#     return Image.fromarray(edges_rgb)

# for i in range(1, 23):
#     img = generate_canny_badge(
#         number=f"{i}",
#         font_path=font_path,
#         save_path=f"/Users/hbin/KTD/pumati-ai/8-pumati-ai/app/model_inference/Canny_image/badge_{i}.png",
#         font_size = 300
#     )
    