import os, logging
from diffusers import StableDiffusionXLControlNetPipeline, ControlNetModel
from dotenv import load_dotenv
from huggingface_hub import login
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = "stabilityai/stable-diffusion-xl-base-1.0"
CONTROLNET_MODEL_ID = "diffusers/controlnet-canny-sdxl-1.0"
DEVICE = device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class SDXLModel:
    _is_authenticated = False

    def __init__(self, controlnet_model_id: str = CONTROLNET_MODEL_ID):
        self._authenticate_huggingface()
        self.pipe = self._load_diffusion_model(controlnet_model_id)
        self.device = DEVICE
        
    def _authenticate_huggingface(self):
        if SDXLModel._is_authenticated:
            return
        load_dotenv()
        token = os.getenv("HF_AUTH_TOKEN")
        if not token:
            raise EnvironmentError("HF_AUTH_TOKEN is not set in .env file.")
        login(token=token)
        SDXLModel._is_authenticated = True

    def _load_diffusion_model(self, controlnet_model_id: str):
        logger.info(f"ControlNet 모델 로드 중: {controlnet_model_id}")
        controlnet = ControlNetModel.from_pretrained(
            controlnet_model_id,
            torch_dtype=torch.float16
        )

        logger.info(f"Stable Diffusion XL + ControlNet 로드 중: {MODEL_NAME}")
        pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
            MODEL_NAME,
            controlnet=controlnet,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True
        ).to(self.device)

        pipe.safety_checker = lambda images, **kwargs: (images, [False] * len(images))
        logger.info("✅ SDXL + ControlNet 파이프라인 로드 완료")
        return pipe
    
badge_creater = SDXLModel()