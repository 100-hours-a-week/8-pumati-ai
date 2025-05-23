import torch

def generate_image(pipe, prompt: str, negative_prompt: str = "realistic, photo, blur, noisy, watermark", seed: int = 42, width: int = 800, height: int = 800):
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
    return result.images[0]
