import os
from PIL import Image
from model_inference.loaders.badge_loader import badge_creater
from context_construction.prompts.badge_prompt import build_badge_prompt
from model_inference.badge_inference_runner import generate_image

SAVE_DIR = "./generated_badges"

class BadgeService:
    def __init__(self):
        self.pipe = badge_creater.load_diffusion_model()
        

    def generate_and_save_badge(self, number: int, filename: str):
        prompt = build_badge_prompt(number)
        image = generate_image(self.pipe, prompt)
        os.makedirs(SAVE_DIR, exist_ok=True)
        image_path = os.path.join(SAVE_DIR, filename)
        image.save(image_path)
        return image_path

    # Todo: implement implanting + controlnet extensions here later

