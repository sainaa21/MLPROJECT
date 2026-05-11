
from fastapi import APIRouter
import pandas as pd

from app.services.extract_video_id import extract_video_id
from app.services.youtube_api import (
    fetch_comments,
    get_video_details
)

router = APIRouter()

@router.get("/fetch-comments")
def fetch_youtube_comments(url: str):

    try:

        video_id = extract_video_id(url)

        if not video_id:
            return {"error": "Invalid YouTube URL"}

        comments = fetch_comments(video_id)

        video_details = get_video_details(video_id)

        df = pd.DataFrame(comments)

        df.to_csv(
            "data/raw/comments.csv",
            index=False
        )

        return {
            "message": "Comments fetched and saved successfully",
            "video_details": video_details,
            "total_comments": len(comments),
            "comments": comments[:10]
        }

    except Exception as e:

        return {
            "error": str(e)
        }


@router.get("/test")
def test_route():
    return {"status": "youtube route works"}

