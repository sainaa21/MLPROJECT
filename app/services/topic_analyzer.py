import logging
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from app.preprocessing.clean_text import clean_comment

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent / "models"
SPAM_MODEL_FILE = MODEL_PATH / "spam_model.pkl"
TFIDF_MODEL_FILE = MODEL_PATH / "tfidf_vectorizer.pkl"


def _prepare_comments(comments: List[str]) -> List[str]:
    logger.debug("Preparing %s raw comments for analysis", len(comments))
    cleaned_comments = []

    for comment in comments:
        if not comment or not isinstance(comment, str):
            continue

        text = str(comment).strip()

        if text == "":
            continue

        normalized = clean_comment(text)

        if normalized:
            cleaned_comments.append(normalized)

    logger.debug("Prepared %s cleaned comments", len(cleaned_comments))
    return cleaned_comments


def _load_spam_classifier():
    if not SPAM_MODEL_FILE.exists() or not TFIDF_MODEL_FILE.exists():
        raise FileNotFoundError(
            "Spam model or vectorizer file not found. "
            "Please ensure app/models/spam_model.pkl and "
            "app/models/tfidf_vectorizer.pkl exist."
        )

    model = joblib.load(SPAM_MODEL_FILE)
    vectorizer = joblib.load(TFIDF_MODEL_FILE)

    return model, vectorizer


def filter_genuine_comments(comments: List[str]) -> List[str]:
    """Return only comments classified as non-spam."""
    comments = _prepare_comments(comments)
    logger.info("Filtering spam from %s prepared comments", len(comments))

    if not comments:
        logger.warning("No comments available for spam filtering")
        return []

    model, vectorizer = _load_spam_classifier()
    transformed = vectorizer.transform(comments)
    predictions = model.predict(transformed)

    genuine = [comments[i] for i, label in enumerate(predictions) if label == 0]
    logger.info("Detected %s genuine comments and %s spam comments", len(genuine), len(comments) - len(genuine))

    return genuine


def extract_keywords(comments: List[str], top_n: int = 30) -> Dict[str, float]:
    """Extract important keywords from genuine comments using TF-IDF."""
    documents = _prepare_comments(comments)
    logger.info("Extracting keywords from %s genuine comments", len(documents))

    if not documents:
        logger.warning("No documents available for keyword extraction")
        return {}

    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),
        max_df=0.85,
        min_df=2,
        max_features=2000
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError as exc:
        logger.error("TF-IDF vectorization failed: %s", exc)
        return {}

    feature_names = vectorizer.get_feature_names_out()
    scores = np.asarray(tfidf_matrix.sum(axis=0)).ravel()

    ranked = sorted(
        zip(feature_names, scores),
        key=lambda pair: pair[1],
        reverse=True
    )[:top_n]

    if not ranked:
        logger.warning("TF-IDF produced no ranked keywords")
        return {}

    max_score = ranked[0][1] or 1.0
    keyword_map = {
        keyword: round(float(score / max_score), 2)
        for keyword, score in ranked
    }

    logger.debug("Top keywords: %s", list(keyword_map.items())[:10])
    return keyword_map


def _build_topic_name(keywords: List[str]) -> str:
    if not keywords:
        return "Generated Topic"

    title_words = [word.capitalize() for word in keywords[:3]]
    return " ".join(title_words)


def _build_topic_description(keywords: List[str]) -> str:
    if not keywords:
        return "Auto-generated topic summary."

    if len(keywords) == 1:
        return f"Comments about {keywords[0]}."

    return (
        f"Comments about {', '.join(keywords[:-1])} "
        f"and {keywords[-1]}."
    )


def _fit_topic_model(document_term_matrix, num_topics: int):
    try:
        lda = LatentDirichletAllocation(
            n_components=num_topics,
            random_state=42,
            learning_method='batch',
            max_iter=20
        )
        lda.fit(document_term_matrix)
        logger.info("LDA topic model fitted with %s topics", num_topics)
        return lda

    except Exception as first_error:
        logger.warning("LDA model failed: %s", first_error)

    try:
        nmf = NMF(
            n_components=num_topics,
            random_state=42,
            max_iter=200
        )
        nmf.fit(document_term_matrix)
        logger.info("NMF fallback model fitted with %s topics", num_topics)
        return nmf

    except Exception as second_error:
        logger.warning("NMF fallback failed: %s", second_error)
        raise RuntimeError("Unable to fit topic model") from second_error


def discover_topics(comments: List[str], num_topics: int = 4) -> List[Dict[str, object]]:
    """Discover the top discussion topics from genuine comments."""
    documents = _prepare_comments(comments)

    if not documents:
        return []

    num_topics = min(num_topics, max(1, len(documents)))

    vectorizer = CountVectorizer(
        stop_words='english',
        max_df=0.9,
        min_df=2,
        max_features=2000
    )

    try:
        doc_term_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return []

    if doc_term_matrix.shape[1] == 0:
        logger.warning("Document-term matrix has zero features")
        return []

    model = _fit_topic_model(doc_term_matrix, num_topics)
    feature_names = vectorizer.get_feature_names_out()

    try:
        document_topic_matrix = model.transform(doc_term_matrix)
    except AttributeError:
        document_topic_matrix = model.fit_transform(doc_term_matrix)

    topic_assignments = np.argmax(document_topic_matrix, axis=1)
    total_documents = len(documents)

    topics = []

    for topic_index in range(num_topics):
        top_term_indices = np.argsort(model.components_[topic_index])[::-1][:6]
        keywords = [feature_names[i] for i in top_term_indices if feature_names[i]]

        comment_count = int(np.sum(topic_assignments == topic_index))
        percentage = round((comment_count / total_documents) * 100, 2)

        topics.append({
            "topic_id": topic_index + 1,
            "name": _build_topic_name(keywords),
            "keywords": keywords,
            "comment_count": comment_count,
            "percentage": percentage,
            "description": _build_topic_description(keywords),
        })

    if not topics:
        logger.warning("Topic discovery returned no topics")
    else:
        logger.info("Discovered %s topics", len(topics))
        logger.debug("Topic summaries: %s", [t["name"] for t in topics])

    return topics


def generate_wordcloud_data(comments: List[str], top_n: int = 100) -> Dict[str, int]:
    """Create keyword frequency data for a frontend word cloud."""
    documents = _prepare_comments(comments)

    if not documents:
        return {}

    vectorizer = CountVectorizer(
        stop_words='english',
        max_df=0.9,
        min_df=2,
        max_features=2000
    )

    try:
        count_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return {}

    counts = np.asarray(count_matrix.sum(axis=0)).ravel()
    feature_names = vectorizer.get_feature_names_out()

    frequencies = {
        feature_names[i]: int(counts[i])
        for i in range(len(feature_names))
        if counts[i] > 0
    }

    sorted_items = sorted(
        frequencies.items(),
        key=lambda item: item[1],
        reverse=True
    )[:top_n]

    if not sorted_items:
        logger.warning("Word cloud frequency extraction returned no terms")
    else:
        logger.info("Generated word cloud data with %s terms", len(sorted_items))

    return dict(sorted_items)
