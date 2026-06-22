from fastapi import APIRouter
import pandas as pd
import joblib

from app.services.extract_video_id import extract_video_id

from app.services.youtube_api import (
    fetch_comments,
    get_video_details
)

from ml.sentiment import analyze_sentiment

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
            "Comments fetched successfully",

            "video_details":
            video_details,

            "total_comments":
            len(comments),

            "comments":
            comments[:10]
        }

    except Exception as e:

        print("FETCH ERROR:", e)

        raise e


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

        if len(comments) == 0:

            return {
                "error": "No comments found"
            }

        comment_texts = []

        for comment in comments:

            if (
                "comment" in comment
                and comment["comment"]
                and isinstance(
                    comment["comment"],
                    str
                )
            ):

                cleaned_comment = (
                    comment["comment"].strip()
                )

                if cleaned_comment != "":

                    comment_texts.append(
                        cleaned_comment
                    )

        if len(comment_texts) == 0:

            return {
                "error":
                "No valid comments found"
            }

        df_comments = pd.DataFrame({

            "comment": comment_texts
        })

        df_comments.to_csv(

            "data/raw/comments.csv",

            index=False
        )

        X = vectorizer.transform(
            comment_texts
        )

        predictions = model.predict(X)

        df = pd.DataFrame({

            "comment": comment_texts,

            "prediction": predictions
        })

        spam_count = int(
            sum(predictions)
        )

        genuine_count = int(
            len(predictions) - spam_count
        )

        total_comments = len(predictions)

        validity_rate = round(

            (genuine_count / total_comments) * 100,

            2
        )

        spam_rate = round(

            (spam_count / total_comments) * 100,

            2
        )

        sentiment_df = df.copy()

        sentiment_df["sentiment"] = sentiment_df[
            "comment"
        ].apply(analyze_sentiment)

        positive_count = len(

            sentiment_df[
                sentiment_df["sentiment"] == "Positive"
            ]
        )

        negative_count = len(

            sentiment_df[
                sentiment_df["sentiment"] == "Negative"
            ]
        )

        neutral_count = len(

            sentiment_df[
                sentiment_df["sentiment"] == "Neutral"
            ]
        )

        return {

            "total_comments":
            total_comments,

            "valid_comments":
            genuine_count,

            "spam_comments":
            spam_count,

            "validity_rate":
            validity_rate,

            "spam_rate":
            spam_rate,

            "good_comments":
            positive_count,

            "bad_comments":
            negative_count,

            "neutral_comments":
            neutral_count,

            "comments":
            sentiment_df.to_dict(
                orient="records"
            )
        }

    except Exception as e:

        print("ANALYZE ERROR:", e)

        raise e


@router.get("/test")
def test_route():

    return {
        "status": "youtube route works"
    }