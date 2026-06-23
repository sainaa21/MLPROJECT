import logging

from fastapi import APIRouter, HTTPException
import pandas as pd

from app.services.topic_analyzer import (
    discover_topics,
    extract_keywords,
    generate_wordcloud_data,
    filter_genuine_comments
)
from app.services.ai_summarizer import generate_audience_summary
from ml.sentiment import analyze_sentiment

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/topics")
def get_topics():
    """Return topic analysis for genuine YouTube comments."""
    logger.info("/topics request started")

    try:
        df = pd.read_csv("data/raw/comments.csv")
        logger.info("Loaded raw comments data with %s rows", len(df))

    except FileNotFoundError:
        logger.error("Comments CSV not found at data/raw/comments.csv")
        raise HTTPException(
            status_code=404,
            detail="No comment data found. Fetch comments first."
        )

    except Exception as exc:
        logger.exception("Unable to read comments data")
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read comments data: {exc}"
        )

    if "comment" not in df.columns:
        logger.error("comments.csv missing required column 'comment'")
        raise HTTPException(
            status_code=400,
            detail="Comment data must include a 'comment' column."
        )

    comments = df["comment"].astype(str).tolist()
    logger.debug("Raw comment count: %s", len(comments))

    genuine_comments = filter_genuine_comments(comments)
    logger.debug("Genuine comment count after spam filtering: %s", len(genuine_comments))

    if not genuine_comments:
        logger.warning("No genuine comments available for topic analysis")
        return {
            "total_comments": len(comments),
            "genuine_comments": 0,
            "topics": [],
            "top_keywords": [],
            "wordcloud": {},
            "message": "No genuine comments available for topic analysis."
        }

    topics = discover_topics(genuine_comments, num_topics=4)
    keyword_scores = extract_keywords(genuine_comments)
    wordcloud = generate_wordcloud_data(genuine_comments)
    sentiment_stats = {
        "positive": len([c for c in genuine_comments if analyze_sentiment(c) == "Positive"]),
        "negative": len([c for c in genuine_comments if analyze_sentiment(c) == "Negative"]),
        "neutral": len([c for c in genuine_comments if analyze_sentiment(c) == "Neutral"]),
    }
    audience_summary = generate_audience_summary(genuine_comments, sentiment_stats, topics)

    top_keywords = [
        {"keyword": keyword, "score": score}
        for keyword, score in list(keyword_scores.items())[:20]
    ]

    logger.info("Returning topic analysis response")

    return {
        "total_comments": len(comments),
        "genuine_comments": len(genuine_comments),
        "topics": topics,
        "top_keywords": top_keywords,
        "wordcloud": wordcloud,
        "audience_summary": audience_summary,
    }


@router.get("/audience-summary")
def get_audience_summary():
    """Return an AI-generated audience summary based on genuine comments."""
    logger.info("/audience-summary request started")

    try:
        df = pd.read_csv("data/raw/comments.csv")
        logger.info("Loaded raw comments data with %s rows", len(df))

    except FileNotFoundError:
        logger.error("Comments CSV not found at data/raw/comments.csv")
        raise HTTPException(
            status_code=404,
            detail="No comment data found. Fetch comments first."
        )

    except Exception as exc:
        logger.exception("Unable to read comments data")
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read comments data: {exc}"
        )

    if "comment" not in df.columns:
        logger.error("comments.csv missing required column 'comment'")
        raise HTTPException(
            status_code=400,
            detail="Comment data must include a 'comment' column."
        )

    comments = df["comment"].astype(str).tolist()
    logger.debug("Raw comment count: %s", len(comments))

    genuine_comments = filter_genuine_comments(comments)
    logger.debug("Genuine comment count after spam filtering: %s", len(genuine_comments))

    sentiment_stats = {
        "positive": 0,
        "negative": 0,
        "neutral": 0
    }

    if genuine_comments:
        for comment in genuine_comments:
            sentiment = analyze_sentiment(comment)
            sentiment_stats["positive"] += 1 if sentiment == "Positive" else 0
            sentiment_stats["negative"] += 1 if sentiment == "Negative" else 0
            sentiment_stats["neutral"] += 1 if sentiment == "Neutral" else 0

    topics = discover_topics(genuine_comments, num_topics=4)
    audience_summary = generate_audience_summary(
        genuine_comments,
        sentiment_stats,
        topics
    )

    logger.info("Returning audience summary response")

    return {
        "total_comments": len(comments),
        "genuine_comments": len(genuine_comments),
        "sentiment_stats": sentiment_stats,
        "topics": topics,
        "audience_summary": audience_summary,
    }
