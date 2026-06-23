import logging

from fastapi import APIRouter
import pandas as pd
import joblib

from app.services.extract_video_id import extract_video_id
from app.services.ai_summarizer import generate_audience_summary
from app.services.topic_analyzer import discover_topics

from app.services.youtube_api import (
    fetch_comments,
    get_video_details
)

from ml.sentiment import analyze_sentiment

logger = logging.getLogger(__name__)
router = APIRouter()

model = joblib.load(
    "app/models/spam_model.pkl"
)

vectorizer = joblib.load(
    "app/models/tfidf_vectorizer.pkl"
)

@router.get("/fetch-comments")
def fetch_youtube_comments(url: str):
    """Fetch YouTube comments and store to data/raw/comments.csv."""
    try:
        logger.info("Fetching comments from URL: %s", url)
        video_id = extract_video_id(url)

        if not video_id:
            logger.warning("Could not extract video ID from URL")
            return {
                "error": "Invalid YouTube URL"
            }

        comments = fetch_comments(video_id)
        logger.info("Fetched %s comments for video: %s", len(comments), video_id)

        video_details = get_video_details(video_id)

        df = pd.DataFrame(comments)

        df.to_csv(
            "data/raw/comments.csv",
            index=False
        )
        logger.debug("Saved comments to data/raw/comments.csv")

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
        logger.exception("FETCH ERROR")
        raise e


@router.post("/analyze")
def analyze(data: dict):
    """Analyze YouTube comments with spam detection and sentiment analysis on genuine comments only."""
    try:
        url = data["url"]
        video_id = extract_video_id(url)

        if not video_id:
            logger.warning("Invalid YouTube URL provided")
            return {
                "error": "Invalid YouTube URL"
            }

        logger.info("Fetching comments for video: %s", video_id)
        comments = fetch_comments(video_id)

        if len(comments) == 0:
            logger.warning("No comments found for video: %s", video_id)
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
            logger.warning("No valid comments found after cleaning")
            return {
                "error":
                "No valid comments found"
            }

        total_comments = len(comment_texts)
        logger.info("Total comments extracted: %s", total_comments)

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

        spam_count = int(
            sum(predictions)
        )

        genuine_count = int(
            len(predictions) - spam_count
        )

        logger.info("Spam detection: %s spam, %s genuine", spam_count, genuine_count)

        validity_rate = round(

            (genuine_count / total_comments) * 100,

            2
        )

        spam_rate = round(

            (spam_count / total_comments) * 100,

            2
        )

        df = pd.DataFrame({

            "comment": comment_texts,

            "prediction": predictions

        })

        genuine_comments_mask = df["prediction"] == 0
        genuine_df = df[genuine_comments_mask].copy()

        logger.debug("Filtering to %s genuine comments for sentiment analysis", len(genuine_df))

        if len(genuine_df) == 0:
            logger.warning("No genuine comments available for sentiment analysis")
            return {
                "total_comments": total_comments,
                "valid_comments": genuine_count,
                "spam_comments": spam_count,
                "validity_rate": validity_rate,
                "spam_rate": spam_rate,
                "good_comments": 0,
                "bad_comments": 0,
                "neutral_comments": 0,
                "message": "No genuine comments for sentiment analysis",
                "comments": []
            }

        genuine_df["sentiment"] = genuine_df[
            "comment"
        ].apply(analyze_sentiment)

        positive_count = len(

            genuine_df[
                genuine_df["sentiment"] == "Positive"
            ]
        )

        negative_count = len(

            genuine_df[
                genuine_df["sentiment"] == "Negative"
            ]
        )

        neutral_count = len(

            genuine_df[
                genuine_df["sentiment"] == "Neutral"
            ]
        )

        logger.info("Sentiment analysis on %s genuine comments: %s positive, %s negative, %s neutral",
                   len(genuine_df), positive_count, negative_count, neutral_count)

        sentiment_stats = {
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count
        }

        genuine_comments_list = genuine_df["comment"].astype(str).tolist()

        logger.info("Discovering topics from %s genuine comments", len(genuine_comments_list))
        topics = discover_topics(genuine_comments_list, num_topics=4)

        logger.info("Generating audience summary")
        audience_summary = generate_audience_summary(
            genuine_comments_list,
            sentiment_stats,
            topics
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

            "audience_summary":
            audience_summary,

            "topics":
            topics,

            "comments":
            genuine_df.to_dict(
                orient="records"
            )
        }

    except Exception as e:
        logger.exception("ANALYZE ERROR")
        raise e


@router.get("/test")
def test_route():

    return {
        "status": "youtube route works"
    }