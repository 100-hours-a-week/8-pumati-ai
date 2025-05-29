from model_inference.loaders.badge_loader import badge_creater
import torch

def generate_image(prompt: str, negative_prompt: str = "realistic, photo, blur, noisy, watermark", seed: int = 42, width: int = 800, height: int = 800):
    generator = torch.Generator("cuda").manual_seed(seed)
    result = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        num_inference_steps=35,
        guidance_scale=7.5,
        generator=generator
    )

    # result = badge_creater.pipe(
    #     prompt=prompt,
    #     image=canny_image,  # controlnet 조건 이미지 (PIL or tensor)
    #     negative_prompt=negative_prompt,
    #     width=width,
    #     height=height,
    #     guidance_scale=7.5,
    #     num_inference_steps=30,
    #     generator=generator
    # )

    return result.images[0]
