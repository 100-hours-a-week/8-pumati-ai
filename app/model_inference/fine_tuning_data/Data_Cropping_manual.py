import streamlit as st
from streamlit_cropper import st_cropper
from PIL import Image, ImageOps
import os
import pandas as pd

# 폴더 설정
image_folder = "./app/model_inference/fine_tuning_data/P_badges"
output_folder = "./app/model_inference/fine_tuning_data/cropped_badges"
os.makedirs(output_folder, exist_ok=True)
csv_path = "./labeled_prompts.csv"

# 리사이즈 함수
def resize_to_square(image: Image.Image, size: int = 800) -> Image.Image:
    return ImageOps.pad(image, (size, size), color="white", centering=(0.5, 0.5))

# 라벨링 CSV 불러오기
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
else:
    df = pd.DataFrame(columns=["filename", "prompt"])

# 이미지 선택
images = [f for f in os.listdir(image_folder) if f.endswith((".jpeg", ".png"))]
current_image = st.selectbox("이미지를 선택하세요", images)

# 세션 상태 초기화
if "crop_count" not in st.session_state or st.session_state.get("last_image") != current_image:
    st.session_state.crop_count = 0
    st.session_state.last_image = current_image

# 이미지 열기
image_path = os.path.join(image_folder, current_image)
img = Image.open(image_path)

st.markdown("### 자를 뱃지 영역을 선택하세요")
cropped_img = st_cropper(img, box_color="#00FFAA", aspect_ratio=(1, 1))
st.image(cropped_img, caption="잘라낸 뱃지 미리보기", use_container_width=True)

# 프롬프트 입력
prompt = st.text_input("프롬프트 (예: a kawaii enamel badge with two hugging mascots)")

# 저장 버튼
if st.button("💾 이 뱃지를 저장하고 다음 자르기 계속하기"):
    crop_filename = f"{os.path.splitext(current_image)[0]}_{st.session_state.crop_count}.png"
    save_path = os.path.join(output_folder, crop_filename)

    resized_img = resize_to_square(cropped_img, size=800)
    resized_img.save(save_path)

    df = pd.concat([df, pd.DataFrame([{"filename": crop_filename, "prompt": prompt}])], ignore_index=True)
    df.to_csv(csv_path, index=False)

    st.success(f"{crop_filename} 저장 완료!")
    st.session_state.crop_count += 1  # 다음 자르기 번호 증가

st.info("같은 이미지에서 여러 개 뱃지를 자르고 싶다면 계속 저장하세요.")
