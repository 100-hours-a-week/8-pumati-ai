# badge_loader.py

import os
from diffusers import ControlNetModel, UniPCMultistepScheduler, StableDiffusionControlNetPipeline #DiffusionPipeline, StableDiffusionXLControlNetImg2ImgPipeline
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv
from huggingface_hub import login
import torch
import logging, psutil

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# "Controlnet -> SDXL -> REFINEMODEL" 구조로, 모델 3개 사용예정.
CONTROLNET_NAME = "lllyasviel/control_v11p_sd15_canny" 
MODEL_NAME = "runwayml/stable-diffusion-v1-5" 
# LORA_PATH = "/content/Badge_M.safetensors"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def print_ram():
    ram = psutil.Process(os.getpid()).memory_info().rss / (1024 ** 3)
    #print(f"[RAM 사용량] {ram:.2f} GB")
    return ram


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
        logger.info(f"허깅페이스 토큰: {token}")
        if not token:
            raise EnvironmentError("HF_AUTH_TOKEN_VICKY is not set in .env file.")
        login(token=token)
        BadgeModel._is_authenticated = True

    async def load_LoRA(self, mod_tags: str) -> None:
        logger.info("5-2) LoRA 다운 설정중...")
        self.base_pipe.scheduler = UniPCMultistepScheduler.from_config(self.base_pipe.scheduler.config) 
        self.base_pipe.unload_lora_weights()

        logger.info(f"5-3 mod_tag: {mod_tags}에 해당하는 LoRA를 불러옵니다.")
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

            self.base_pipe.set_adapters(["wood1", "wood2"], adapter_weights=[0.8, 0.2])

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
            logger.info(f"mod_tags가 {mod_tags}이므로 원본 이미지 생성을 시작합니다. {print_ram()} GB")
            print_ram()
            lora_original1 = hf_hub_download(repo_id="HHBeen/badge_LoRA", filename="First_Original.safetensors")
            lora_original2 = hf_hub_download(repo_id="HHBeen/badge_LoRA", filename="Third_Original.safetensors")

            self.base_pipe.load_lora_weights(lora_original1, adapter_name="Original1")
            self.base_pipe.load_lora_weights(lora_original2, adapter_name="Original2")
            

            self.base_pipe.set_adapters(["Original1", "Original2"], adapter_weights=[0.1, 0.9])
            

        logger.info(f"5-4 LoRA 로드 완료 {print_ram()}")
        def dummy_checker(images, **kwargs):
            return images, [False] * len(images)
        
        self.base_pipe.safety_checker = dummy_checker

    def load_diffusion_model(self) -> None:
        logger.info("6-1-1) Controlnet파이프라인 로드")
        controlnet_pipe = ControlNetModel.from_pretrained(
            CONTROLNET_NAME,
            torch_dtype=torch.float16 if DEVICE.type == "cuda" else torch.float32,
        ).to(DEVICE)

        # 2) SDXL파이프라인 로드
        logger.info("6-1-2) SD1.5파이프라인 로드")
        self.base_pipe = StableDiffusionControlNetPipeline.from_pretrained(
            MODEL_NAME,
            controlnet=controlnet_pipe,
            torch_dtype=torch.float16
        ).to(DEVICE)

        self.base_pipe.enable_model_cpu_offload()

    
badge_loader_instance = BadgeModel()
badge_loader_instance.load_diffusion_model()
