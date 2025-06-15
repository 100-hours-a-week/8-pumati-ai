# badge_loader.py

import os
from diffusers import ControlNetModel, StableDiffusionXLControlNetImg2ImgPipeline, UniPCMultistepScheduler #DiffusionPipeline
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv
from huggingface_hub import login
import torch
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# "Controlnet -> SDXL -> REFINEMODEL" 구조로, 모델 3개 사용예정.
CONTROLNET_NAME = "lllyasviel/control_v11p_sd15_canny" 
MODEL_NAME = "runwayml/stable-diffusion-v1-5" 
LORA_PATH = "/content/Badge_M.safetensors"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class BadgeModel:
    _is_authenticated = False

    def __init__(self):
        self._authenticate_huggingface()
        self.base_pipe = None
        #self.refine_pipe = None
        
    def _authenticate_huggingface(self):
        if BadgeModel._is_authenticated:
            return
        load_dotenv()
        token = os.getenv("HF_AUTH_TOKEN_VICKY")
        if not token:
            raise EnvironmentError("HF_AUTH_TOKEN is not set in .env file.")
        login(token=token)
        BadgeModel._is_authenticated = True

    def load_LoRA(self, mod_tags: str) -> None:
        self.base_pipe.scheduler = UniPCMultistepScheduler.from_config(self.base_pipe.scheduler.config)
        self.base_pipe.unload_lora_weights()

        if mod_tags == "뉴스":
            lora_news = hf_hub_download(repo_id="HHBeen/badge_LoRA", filename="First_news.safetensors")

            self.base_pipe.load_lora_weights(lora_news)

        elif mod_tags == "자연 풍경":
            lora_snow = hf_hub_download(repo_id="HHBeen/badge_LoRA", filename="First_snow.safetensors")

            self.base_pipe.load_lora_weights(lora_snow)

        elif mod_tags == "우드":
            lora_wood1 = hf_hub_download(repo_id="HHBeen/badge_LoRA", filename="First_wood.safetensors")
            lora_wood2 = hf_hub_download(repo_id="HHBeen/badge_LoRA", filename="Second_Original.safetensors")

            self.base_pipe.load_lora_weights(lora_wood1, adapter_name="wood1")
            self.base_pipe.load_lora_weights(lora_wood2, adapter_name="wood2")

            self.base_pipe.load_lora_weights(["wood1", "wood2"], adapter_weights=[0.8, 0.2])

        elif mod_tags == "픽셀":
            lora_pixel1 = hf_hub_download(repo_id="HHBeen/badge_LoRA", filename="First_pixel.safetensors")
            lora_pixel2 = hf_hub_download(repo_id="HHBeen/badge_LoRA", filename="Second_pixel.safetensors")

            self.base_pipe.load_lora_weights(lora_pixel1, adapter_name="pixel1")
            self.base_pipe.load_lora_weights(lora_pixel2, adapter_name="pixel2")

            self.base_pipe.set_adapters(["pixel1", "pixel2"], adapter_weights=[0.3, 0.7])

        elif mod_tags == "게임":
            lora_game = hf_hub_download(repo_id="HHBeen/badge_LoRA", filename="First_game_effect.safetensors")

            self.base_pipe.load_lora_weights(lora_game)

        else:
            lora_original1 = hf_hub_download(repo_id="HHBeen/badge_LoRA", filename="First_Original.safetensors")
            lora_original2 = hf_hub_download(repo_id="HHBeen/badge_LoRA", filename="Second_Original.safetensors")

            self.base_pipe.load_lora_weights(lora_original1, adapter_name="Original1")
            self.base_pipe.load_lora_weights(lora_original2, adapter_name="Original2")

            self.base_pipe.set_adapters(["Original1", "Original2"], adapter_weights=[0.8, 0.2])

        def dummy_checker(images, **kwargs):
            return images, [False] * len(images)
        
        self.base_pipe.safety_checker = dummy_checker

    def load_diffusion_model(self) -> None:
        controlnet_pipe = ControlNetModel.from_pretrained(
            CONTROLNET_NAME,
            torch_dtype=torch.float16 if DEVICE.type == "cuda" else torch.float32,
        ).to(DEVICE)

        # 2) SDXL파이프라인 로드
        logger.info("6-1-1) SDXL파이프라인 로드")
        self.base_pipe = StableDiffusionXLControlNetImg2ImgPipeline.from_pretrained(
            MODEL_NAME,
            controlnet=controlnet_pipe,
            torch_dtype=torch.float16
        ).to(DEVICE)


        
    
badge_loader_instance = BadgeModel()
badge_loader_instance.load_diffusion_model()
