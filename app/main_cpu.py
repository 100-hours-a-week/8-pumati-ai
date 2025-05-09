from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
#from fast_api.endpoints.fortune_router import router as fortune_router
from fast_api.endpoints.comment_router import comment_app as comment_router
import uvicorn

#FastAPI 태그설정
app = FastAPI()

# CORS 미들웨어 설정
# 프로덕션 환경에서는 실제 도메인으로 제한하는 것이 좋습니다
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용 (프로덕션에서는 특정 도메인으로 제한 권장)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

#app.include_router(fortune_router, prefix="/api/llm", tags=["Fortune"])
app.include_router(comment_router, tags=["Comment"])

if __name__ == "__main__":
    uvicorn.run("main_cpu:app", host="0.0.0.0", port=8080, reload=False)
