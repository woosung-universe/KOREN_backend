from fastapi import FastAPI
from app.routers import router

app = FastAPI()

# 라우터 등록
app.include_router(router)
