from app.fast_api.schemas.badge_schemas import BadgeRequest #입력데이터
from app.context_construction.prompts.badge_prompt import BadgePrompt #프롬프트(더미데이터 로드)
from app.model_inference.loaders.badge_loader import badge_loader_instance #모델 파이프라인 로드

import torch
from PIL import Image
from typing import List

def generate_image(mod_tags: str, team_number: int, request_data: BadgeRequest, negative_prompt: str = "realistic, photo, blur, noisy, watermark", seed: int = 42, width: int = 800, height: int = 800):
    generator = torch.Generator("cuda").manual_seed(seed)

    # 1) 프롬프트 로드
    prompt_instance = BadgePrompt(request_data)
    prompt = prompt_instance.build_badge_prompt(mod_tags, team_number)

    # 2) pipline로드
    SDXL_pipe, refine_pipe = badge_loader_instance.load_diffusion_model()

    #3) Controlnet 이미지 로드
    controlnet_path= f"./model_inference/Canny_image/badge_{team_number}.png"
    control_image = Image.open(controlnet_path).convert("RGB")

    # 4) 결과이미지 출력
    SDXL_result = SDXL_pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        image=control_image,
        num_inference_steps=35,
        guidance_scale=7.5,
        generator=generator
    ).images[0]

    refined_image = refine_pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=SDXL_result,
        num_inference_steps=20,
        guidance_scale=7.5,
        denoising_start=0.8
    ).images[0]

    return refined_image