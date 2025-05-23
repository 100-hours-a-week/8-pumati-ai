from diffusers import DiffusionPipeline
import torch

MODEL_NAME = "stabilityai/stable-diffusion-xl-base-1.0"

def load_diffusion_model():
    pipe = DiffusionPipeline.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True
    )
    pipe = pipe.to("cuda")
    pipe.safety_checker = lambda images, **kwargs: (images, [False] * len(images))
    return pipe