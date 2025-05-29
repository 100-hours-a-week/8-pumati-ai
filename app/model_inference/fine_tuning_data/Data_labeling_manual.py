# app.py
import streamlit as st
import os
import pandas as pd

# 설정
image_folder = "/Users/hbin/KTD/pumati-ai/8-pumati-ai/app/model_inference/fine_tuning_data/badges"
csv_path = "./app/model_inference/fine_tuning_data/labeled_prompts.csv"

# 이미지 리스트 불러오기
image_files = sorted([f for f in os.listdir(image_folder) if f.endswith((".jpg", ".png"))])

# 이미 라벨링된 건 제외
if os.path.exists(csv_path):
    labeled_df = pd.read_csv(csv_path)
    labeled_files = set(labeled_df["filename"])
else:
    labeled_df = pd.DataFrame(columns=["filename", "prompt"])
    labeled_files = set()

unlabeled_files = [f for f in image_files if f not in labeled_files]

# Streamlit UI
st.title("📛 뱃지 라벨링 툴")
if unlabeled_files:
    current_file = unlabeled_files[0]
    st.image(os.path.join(image_folder, current_file), caption=current_file, use_container_width=True)
    prompt = st.text_input("📝 이 뱃지에 어울리는 프롬프트를 입력하세요:")

    if st.button("✅ 저장"):
        new_row = {"filename": current_file, "prompt": prompt}
        labeled_df = pd.concat([labeled_df, pd.DataFrame([new_row])], ignore_index=True)
        labeled_df.to_csv(csv_path, index=False)
        st.success(f"{current_file} 저장됨! 다음 이미지로 이동하세요.")
        st.experimental_rerun()
else:
    st.success("🎉 모든 이미지 라벨링 완료!")
