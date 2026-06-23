import json
import os
import requests

BASE_URL = os.getenv("TOPIC_API_URL", "http://127.0.0.1:8000")
ENDPOINT = "/topics"


def test_topics_endpoint():
    url = BASE_URL + ENDPOINT
    response = requests.get(url)

    print("Request URL:", url)
    print("Status code:", response.status_code)

    try:
        payload = response.json()
    except ValueError:
        print("Response is not valid JSON")
        print(response.text)
        return

    print(json.dumps(payload, indent=2))

    print("\nValidation checks:")
    print("- total_comments:", payload.get("total_comments"))
    print("- genuine_comments:", payload.get("genuine_comments"))
    print("- topics count:", len(payload.get("topics", [])))
    print("- top_keywords count:", len(payload.get("top_keywords", [])))
    print("- wordcloud terms:", len(payload.get("wordcloud", {})))

    for i, topic in enumerate(payload.get("topics", []), start=1):
        print(f"Topic {i}: {topic.get('name')}")
        print(f"  keywords: {topic.get('keywords')}")
        print(f"  comment_count: {topic.get('comment_count')}")
        print(f"  percentage: {topic.get('percentage')}")


if __name__ == "__main__":
    test_topics_endpoint()
