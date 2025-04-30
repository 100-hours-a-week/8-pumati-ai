from fastapi import FastAPI
from fast_api.endpoints.fortune_router import router as fortune_router
import uvicorn

app = FastAPI()
app.include_router(fortune_router, tags=["Fortune"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
