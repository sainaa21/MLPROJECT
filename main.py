import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.youtube_routes import router as youtube_router
from app.routes.topic_routes import router as topic_router
from app.routes.comment_routes import router as comment_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(youtube_router)
app.include_router(topic_router)
app.include_router(comment_router)

@app.get("/")
def home():
    return {
        "message": "YouTube Insight AI Running"
    }