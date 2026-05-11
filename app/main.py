from fastapi import FastAPI
from app.routes.youtube import router

app = FastAPI()

app.include_router(router)

@app.get("/")
def home():
    return {"message": "YouTube Insight AI Running"}