import os
from diffusers import ControlNetModel, StableDiffusionXLControlNetImg2ImgPipeline, DiffusionPipeline
from dotenv import load_dotenv
from huggingface_hub import login
import torch
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# "Controlnet -> SDXL -> REFINEMODEL" 구조로, 모델 3개 사용예정.
CONTROLNET_NAME = "diffusers/controlnet-canny-sdxl-1.0-small"
MODEL_NAME = "stabilityai/stable-diffusion-xl-base-1.0"
REFINEMODEL_NAME = "stabilityai/stable-diffusion-xl-refiner-1.0"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class BadgeModel:
    _is_authenticated = False

    def __init__(self):
        self._authenticate_huggingface()
        self.SDXL_pipe = None
        self.refine_pipe = None
        
    def _authenticate_huggingface(self):
        if BadgeModel._is_authenticated:
            return
        load_dotenv()
        token = os.getenv("HF_AUTH_TOKEN_VICKY")
        if not token:
            raise EnvironmentError("HF_AUTH_TOKEN is not set in .env file.")
        login(token=token)
        BadgeModel._is_authenticated = True

    def load_diffusion_model(self):
        if self.SDXL_pipe is None:  # 한 번만 로드  
            # 1) controlnet 파이프라인 로드
            
            controlnet_pipe = ControlNetModel.from_pretrained(
                CONTROLNET_NAME,
                torch_dtype=torch.float16 if DEVICE.type == "cuda" else torch.float32,
            ).to(DEVICE)

            # 2) SDXL파이프라인 로드
            logger.info("6-1-1) SDXL파이프라인 로드")
            self.SDXL_pipe = StableDiffusionXLControlNetImg2ImgPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                controlnet=controlnet_pipe,
                torch_dtype=torch.float16
            ).to(DEVICE)

            # 3) refine파이프라인 로드
            logger.info("6-1-2) refine파이프라인 로드")
            self.refine_pipe = DiffusionPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-refiner-1.0",
                text_encoder_2=self.SDXL_pipe.text_encoder_2,
                vae=self.SDXL_pipe.vae,
                torch_dtype=torch.float16,
                use_safetensors=True,
                variant="fp16"
            ).to(DEVICE)

            self.SDXL_pipe.safety_checker = lambda images, **kwargs: (images, [False] * len(images))
            return self.SDXL_pipe, self.refine_pipe
        else:
            return self.SDXL_pipe, self.refine_pipe
    
badge_loader_instance = BadgeModel()
SDXL_pipe, refine_pipe = badge_loader_instance.load_diffusion_model()
