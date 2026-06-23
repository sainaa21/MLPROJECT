import logging
import os
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def _initialize_gemini_client():
    """Initialize Google Gemini client with API key."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not found in environment variables")
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        return genai
    except ImportError:
        logger.error("google-generativeai package not installed")
        return None
    except Exception as exc:
        logger.error("Failed to initialize Gemini client: %s", exc)
        return None


def _build_summary_prompt(
    sample_comments: List[str],
    sentiment_stats: Dict[str, int],
    topics: List[Dict[str, object]]
) -> str:
    """Build a detailed prompt for Gemini to generate audience summary."""
    
    comments_section = "\n".join([f"- {comment[:150]}" for comment in sample_comments[:20]])

    sentiment_total = sum(sentiment_stats.values())
    sentiment_percentages = {
        k: round((v / sentiment_total * 100), 1) if sentiment_total > 0 else 0
        for k, v in sentiment_stats.items()
    }

    topics_section = "\n".join([
        f"- {topic.get('name', 'Unknown')}: {', '.join(topic.get('keywords', [])[:5])}"
        for topic in topics[:5]
    ])

    prompt = f"""Analyze the YouTube video comments below and generate a concise audience intelligence summary.

SAMPLE COMMENTS:
{comments_section}

SENTIMENT DISTRIBUTION:
- Positive: {sentiment_stats.get('positive', 0)} ({sentiment_percentages.get('positive', 0)}%)
- Negative: {sentiment_stats.get('negative', 0)} ({sentiment_percentages.get('negative', 0)}%)
- Neutral: {sentiment_stats.get('neutral', 0)} ({sentiment_percentages.get('neutral', 0)}%)

MAIN DISCUSSION TOPICS:
{topics_section}

Based on this data, generate a 100-150 word professional summary that includes:
1. Overall audience mood and engagement level
2. Main discussion themes and what viewers appreciate most
3. Positive feedback highlights
4. Criticisms or concerns mentioned
5. Final insight about the audience's perception

Format as a single coherent paragraph (no bullet points). Be specific and reference the actual comments and topics provided."""

    return prompt


def _generate_fallback_summary(
    sentiment_stats: Dict[str, int],
    topics: List[Dict[str, object]]
) -> str:
    """Generate a fallback summary when Gemini API fails."""
    
    total = sum(sentiment_stats.values())
    if total == 0:
        return "Unable to generate audience summary due to insufficient data."

    positive_pct = round((sentiment_stats.get('positive', 0) / total * 100), 1)
    negative_pct = round((sentiment_stats.get('negative', 0) / total * 100), 1)

    primary_topic = topics[0].get('name', 'general discussion') if topics else 'general discussion'

    if positive_pct > 60:
        mood = "predominantly positive"
    elif negative_pct > 40:
        mood = "mixed or critical"
    else:
        mood = "neutral"

    fallback = (
        f"The audience sentiment is {mood}, with {positive_pct}% positive comments. "
        f"The primary discussion theme centers around {primary_topic}. "
        f"Viewers are actively engaged with the content and sharing feedback across multiple topics."
    )

    return fallback


def generate_audience_summary(
    genuine_comments: List[str],
    sentiment_stats: Dict[str, int],
    topics: List[Dict[str, object]]
) -> str:
    """
    Generate an AI-powered audience intelligence summary using Google Gemini.
    
    Args:
        genuine_comments: List of non-spam comment texts
        sentiment_stats: Dict with counts: {"positive": int, "negative": int, "neutral": int}
        topics: List of topic dicts with "name" and "keywords"
    
    Returns:
        A concise paragraph summarizing audience insights (100-150 words)
    """
    
    if not genuine_comments:
        logger.warning("No genuine comments provided for summary generation")
        return "No genuine comments available to generate audience summary."

    if not sentiment_stats or sum(sentiment_stats.values()) == 0:
        logger.warning("No sentiment data provided for summary generation")
        return "Insufficient sentiment data to generate audience summary."

    logger.info("Generating audience summary for %s genuine comments", len(genuine_comments))

    sample_comments = genuine_comments[:200]

    genai = _initialize_gemini_client()

    if not genai:
        logger.warning("Gemini client not available, using fallback summary")
        return _generate_fallback_summary(sentiment_stats, topics)

    try:
        prompt = _build_summary_prompt(sample_comments, sentiment_stats, topics)
        logger.debug("Built Gemini prompt with %s sample comments", len(sample_comments))

        model = genai.GenerativeModel("gemini-pro")

        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 256,
                "temperature": 0.7,
            }
        )

        summary = response.text.strip()
        logger.info("Generated audience summary successfully: %s chars", len(summary))

        if len(summary) < 50:
            logger.warning("Generated summary is very short, using fallback")
            return _generate_fallback_summary(sentiment_stats, topics)

        return summary

    except Exception as exc:
        logger.exception("Gemini API call failed: %s", exc)
        return _generate_fallback_summary(sentiment_stats, topics)
