import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
import pandas as pd
import joblib

from app.preprocessing.clean_text import clean_comment
from ml.sentiment import analyze_sentiment

logger = logging.getLogger(__name__)
router = APIRouter()

# Load models at module import for performance
try:
    spam_model = joblib.load("app/models/spam_model.pkl")
    tfidf_vectorizer = joblib.load("app/models/tfidf_vectorizer.pkl")
except Exception as e:
    logger.warning("Could not load spam model/vectorizer at import: %s", e)
    spam_model = None
    tfidf_vectorizer = None


@router.get("/comments")
def get_comments(
    search: Optional[str] = Query(None, description="Search text in comment"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment: Positive|Negative|Neutral"),
    spam_status: Optional[str] = Query(None, description="Filter by spam status: Spam|Genuine"),
    sort_by: Optional[str] = Query(None, description="Sort by: newest|oldest|likes"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
):
    """Return all analyzed comments with filtering, search, sorting, and pagination."""
    try:
        df = pd.read_csv("data/raw/comments.csv")
    except FileNotFoundError:
        logger.error("Comments CSV not found: data/raw/comments.csv")
        raise HTTPException(status_code=404, detail="No comment data found. Please fetch comments first.")
    except Exception as exc:
        logger.exception("Failed reading comments CSV: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    # Ensure required columns exist and fill defaults
    if "comment" not in df.columns:
        logger.error("comments.csv missing required 'comment' column")
        raise HTTPException(status_code=400, detail="Comment CSV missing 'comment' column")

    for col in ("author", "likes", "published_at"):
        if col not in df.columns:
            df[col] = None

    total_comments = len(df)
    logger.info("Loaded %s total comments", total_comments)

    # Prepare cleaned text for spam prediction and search
    df["_cleaned"] = df["comment"].astype(str).apply(clean_comment)

    # Load models if not loaded
    global spam_model, tfidf_vectorizer
    if spam_model is None or tfidf_vectorizer is None:
        try:
            spam_model = joblib.load("app/models/spam_model.pkl")
            tfidf_vectorizer = joblib.load("app/models/tfidf_vectorizer.pkl")
        except Exception as e:
            logger.exception("Spam model or vectorizer not available: %s", e)
            raise HTTPException(status_code=500, detail="Spam model or vectorizer not found")

    # Predict spam for all comments
    try:
        X = tfidf_vectorizer.transform(df["_cleaned"].astype(str).tolist())
        preds = spam_model.predict(X)
        df["spam_status"] = ["Spam" if int(p) == 1 else "Genuine" for p in preds]
        logger.info("Completed spam predictions: %s spam, %s genuine", int(sum(preds)), int(len(preds)-sum(preds)))
    except Exception as exc:
        logger.exception("Spam prediction failed: %s", exc)
        raise HTTPException(status_code=500, detail="Spam prediction failed")

    # Sentiment: only for Genuine comments
    df["sentiment"] = None
    try:
        genuine_mask = df["spam_status"] == "Genuine"
        df.loc[genuine_mask, "sentiment"] = df.loc[genuine_mask, "comment"].astype(str).apply(analyze_sentiment)
        pos = int((df["sentiment"] == "Positive").sum())
        neg = int((df["sentiment"] == "Negative").sum())
        neu = int((df["sentiment"] == "Neutral").sum())
        logger.info("Sentiment on genuine comments: %s positive, %s negative, %s neutral", pos, neg, neu)
    except Exception as exc:
        logger.exception("Sentiment analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail="Sentiment analysis failed")

    # Apply search filter
    filtered = df
    if search:
        search_lower = str(search).lower()
        filtered = filtered[filtered["comment"].astype(str).str.lower().str.contains(search_lower, na=False)]
        logger.debug("Applied search filter '%s' -> %s rows", search, len(filtered))

    # Apply sentiment filter
    if sentiment:
        sentiment = sentiment.capitalize()
        if sentiment not in ("Positive", "Negative", "Neutral"):
            raise HTTPException(status_code=400, detail="Invalid sentiment filter")
        filtered = filtered[filtered["sentiment"] == sentiment]
        logger.debug("Applied sentiment filter '%s' -> %s rows", sentiment, len(filtered))

    # Apply spam_status filter
    if spam_status:
        spam_status = spam_status.capitalize()
        if spam_status not in ("Spam", "Genuine"):
            raise HTTPException(status_code=400, detail="Invalid spam_status filter")
        filtered = filtered[filtered["spam_status"] == spam_status]
        logger.debug("Applied spam_status filter '%s' -> %s rows", spam_status, len(filtered))

    filtered_count = len(filtered)

    # Sorting
    if sort_by:
        sort_by = sort_by.lower()
        if sort_by == "likes":
            # coerce likes to numeric
            filtered["likes"] = pd.to_numeric(filtered["likes"], errors="coerce").fillna(0).astype(int)
            filtered = filtered.sort_values(by="likes", ascending=False)
        elif sort_by == "newest":
            filtered["_ts"] = pd.to_datetime(filtered["published_at"], errors="coerce")
            filtered = filtered.sort_values(by="_ts", ascending=False)
        elif sort_by == "oldest":
            filtered["_ts"] = pd.to_datetime(filtered["published_at"], errors="coerce")
            filtered = filtered.sort_values(by="_ts", ascending=True)
        else:
            raise HTTPException(status_code=400, detail="Invalid sort_by value")
        logger.debug("Applied sorting by %s", sort_by)

    # Pagination
    start = (page - 1) * limit
    end = start + limit
    page_df = filtered.iloc[start:end]

    # Build response comments
    comments_out = []
    for _, row in page_df.iterrows():
        comments_out.append({
            "author": row.get("author") if pd.notna(row.get("author")) else None,
            "comment": row.get("comment"),
            "likes": int(row.get("likes")) if pd.notna(row.get("likes")) else 0,
            "published_at": row.get("published_at"),
            "spam_status": row.get("spam_status"),
            "sentiment": row.get("sentiment") if pd.notna(row.get("sentiment")) else None,
        })

    return {
        "total_comments": total_comments,
        "filtered_comments": filtered_count,
        "page": page,
        "limit": limit,
        "comments": comments_out,
    }
