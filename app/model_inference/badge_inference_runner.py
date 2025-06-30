#badge_inference_runner.py

from app.fast_api.schemas.badge_schemas import BadgeRequest #입력데이터
from app.context_construction.prompts.badge_prompt import BadgePrompt #프롬프트(더미데이터 로드)
from app.model_inference.loaders.badge_loader import badge_loader_instance #모델 파이프라인 로드

import torch
from PIL import Image
from typing import List

import logging, asyncio, gc

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# async def get_model(mod_tags: str):
#     #await badge_loader_instance.load_diffusion_model()
#     await badge_loader_instance.load_LoRA(mod_tags)

async def generate_image(mod_tags: str, team_number: int, request_data: BadgeRequest, negative_prompt: str = "realistic, photo, blur, noisy, watermark", seed: int = 42, width: int = 512, height: int = 512):
    generator = torch.Generator("cuda").manual_seed(seed)

    logger.info("3-2) Canny이미지 로드, 프롬프트 불러오기")
    # 1) Canny이미지, 프롬프트 로드
    badge_input_instance = BadgePrompt(request_data)
    logger.info("5-1) 이미지 생성 시작: 허깅페이스에서 LoRA 다운중...")
    # badge_canny = badge_input_instance.insert_logo_on_badge()

    badge_canny, _ = await asyncio.gather(
        badge_input_instance.insert_logo_on_badge(),
        badge_loader_instance.load_LoRA(mod_tags)#get_model(mod_tags=mod_tags)
    )
    # 2) pipline로드
    # get_model(mod_tags = mod_tags)

    control_image = Image.fromarray(badge_canny).convert("L")
    prompt = badge_input_instance.build_badge_prompt(mod_tags, team_number)
    negative_prompt = "dark colors, gray, brown, metallic shadows, english, watermark, distortion, blurry"
    
    # 3) 결과이미지 출력
    logger.info("6-1) 이미지 생성중: Controlnet + base 이미지 모델 동작 시작")
    base_result = badge_loader_instance.base_pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        image=control_image,
        num_inference_steps=30,
        guidance_scale=7.5,
        generator=generator
    ).images[0]

    del badge_input_instance, badge_canny, control_image, prompt, generator 
    gc.collect()

    return base_result