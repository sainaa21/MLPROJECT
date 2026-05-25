from fastapi import APIRouter
import pandas as pd
import joblib

from app.services.extract_video_id import extract_video_id
from app.services.youtube_api import (
    fetch_comments,
    get_video_details
)

router = APIRouter()

model = joblib.load(
    "app/models/spam_model.pkl"
)

vectorizer = joblib.load(
    "app/models/tfidf_vectorizer.pkl"
)

@router.get("/fetch-comments")
def fetch_youtube_comments(url: str):

    try:

        video_id = extract_video_id(url)

        if not video_id:

            return {
                "error": "Invalid YouTube URL"
            }

        comments = fetch_comments(video_id)

        video_details = get_video_details(video_id)

        df = pd.DataFrame(comments)

        df.to_csv(
            "data/raw/comments.csv",
            index=False
        )

        return {

            "message":
            "Comments fetched and saved successfully",

            "video_details":
            video_details,

            "total_comments":
            len(comments),

            "comments":
            comments[:10]
        }

    except Exception as e:

        return {
            "error": str(e)
        }

@router.post("/analyze")
def analyze(data: dict):

    try:

        url = data["url"]

        video_id = extract_video_id(url)

        if not video_id:

            return {
                "error": "Invalid YouTube URL"
            }

        comments = fetch_comments(video_id)

        comment_texts = []

        for comment in comments:

            if "comment" in comment:

                comment_texts.append(
                    comment["comment"]
                )

        X = vectorizer.transform(
            comment_texts
        )

        predictions = model.predict(X)

        spam_count = int(
            sum(predictions)
        )

        valid_count = int(
            len(predictions) - spam_count
        )

        total_comments = len(predictions)

        validity_rate = round(
            (valid_count / total_comments) * 100,
            2
        )

        spam_rate = round(
            (spam_count / total_comments) * 100,
            2
        )

        good_comments = 0

        neutral_comments = 0

        bad_comments = 0

        return {

            "total_comments":
            total_comments,

            "valid_comments":
            valid_count,

            "spam_comments":
            spam_count,

            "validity_rate":
            validity_rate,

            "good_comments":
            good_comments,

            "neutral_comments":
            neutral_comments,

            "bad_comments":
            bad_comments,

            "spam_rate":
            spam_rate,

            "summary":
            "Real ML spam analysis completed successfully."
        }

    except Exception as e:

        return {
            "error": str(e)
        }

@router.get("/test")
def test_route():

    return {
        "status": "youtube route works"
    }