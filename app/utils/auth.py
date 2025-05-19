# app/utils/auth.py

import os
from dotenv import load_dotenv
from huggingface_hub import login
import logging

logger = logging.getLogger(__name__)

_is_authenticated = False

def authenticate_huggingface():
    global _is_authenticated
    if _is_authenticated:
        logger.info("Hugging Face 인증 이미 완료됨.")
        return

    load_dotenv()
    token = os.getenv("HF_AUTH_TOKEN")
    if not token:
        raise EnvironmentError("HF_AUTH_TOKEN is not set in .env file.")
    login(token=token)
    _is_authenticated = True
    logger.info("Hugging Face 인증 완료.")
