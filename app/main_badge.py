from fastapi import FastAPI
import uvicorn
from app.fast_api.endpoints.image_router import app_badge as badge_router
from app.fast_api.endpoints.report_router import app_report as report_router

app_badge = FastAPI()
app_badge.include_router(badge_router, tags=["badge"])
app_badge.include_router(report_router, tags=["report"])

@app_badge.get("/healthz")
async def healthz():
    return {"status": "ok", "message": "API is running"}


if __name__ == "__main__":
    uvicorn.run("app.main_badge:app_badge", host="0.0.0.0", port=8080, reload=True)
   #uvicorn.run("app.main_badge:app_badge", host="0.0.0.0", port=8080, reload=True)

# vsc 실행방법: 프로젝트 루트에서 실행 커맨드
# uvicorn app.main_badge:app_badge --host 0.0.0.0 --port 8000 --reload
