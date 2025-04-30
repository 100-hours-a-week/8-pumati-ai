from pydantic import BaseModel

class FortuneRequest(BaseModel):
    memberId: int
    course: str
    date: str
