from fastapi import FastAPI
from app.fast_api.endpoints.fortune_router import router as fortune_router
# from app.fast_api.endpoints.comment_router import comment_app as comment_router
import uvicorn

#FastAPI 태그설정
app = FastAPI()
app.include_router(fortune_router, prefix="/api/llm", tags=["Fortune"])
# app.include_router(comment_router, tags=["Comment"])

# 추가: /healthz 엔드포인트, 헬스체크용
@app.get("/healthz")
async def healthz():
    return {"status": "ok", "message": "API is running"}

if __name__ == "__main__":
    uvicorn.run("app.main_gpu:app", host="0.0.0.0", port=8080, reload=True)

# vsc 실행방법: 프로젝트 루트에서 실행 커맨드
# uvicorn app.main_gpu:app --reload