
from fastapi import FastAPI
from app.api.routers import songs, users  # 導入 users 路由

app = FastAPI()

app.include_router(songs.router)
app.include_router(users.router)  # 新增：包含用戶推薦路由


@app.get("/")
async def root():
    return {"message": "Hello Music Recommendation System!"}
