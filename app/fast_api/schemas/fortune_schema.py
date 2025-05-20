# app/fast_api/schemas/fortune_schema.py
# 요청 및 응답 데이터 형식을 정의

from pydantic import BaseModel
from typing import Literal, Dict
from typing import Optional

from pydantic import BaseModel

class FortuneRequest(BaseModel):
    name: str
    course: Optional[str] = None
    date: str

class FortuneResponse(BaseModel):
    message: str
    data: dict