from fastapi import FastAPI
import uvicorn
from app.fast_api.endpoints.image_router import app_badge as badge_router

app_badge = FastAPI()
app_badge.include_router(badge_router, tags=["badge"])

@app_badge.get("/healthz")
async def healthz():
    return {"status": "ok", "message": "API is running"}


if __name__ == "__main__":
    uvicorn.run("app.main_badge:app_badge", host="0.0.0.0", port=8080, reload=True)