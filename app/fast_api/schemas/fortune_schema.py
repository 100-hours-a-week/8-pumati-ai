# app/fast_api/schemas/fortune_schema.py
from pydantic import BaseModel
from typing import Literal, Dict

from pydantic import BaseModel

class FortuneRequest(BaseModel):
    memberId: int
    course: str
    date: str

class FortuneResponse(BaseModel):
    message: str
    data: dict