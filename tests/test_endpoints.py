import json
import os
import sys
import requests

BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

ENDPOINTS = {
    "fetch_comments": {
        "method": "GET",
        "path": "/fetch-comments",
        "params": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        "required_fields": ["message", "video_details", "total_comments", "comments"]
    },
    "analyze": {
        "method": "POST",
        "path": "/analyze",
        "json": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        "required_fields": ["total_comments", "valid_comments", "spam_comments", "good_comments", "bad_comments", "neutral_comments", "audience_summary", "topics", "comments"]
    },
    "topics": {
        "method": "GET",
        "path": "/topics",
        "required_fields": ["total_comments", "genuine_comments", "topics", "top_keywords", "wordcloud", "audience_summary"]
    },
    "audience_summary": {
        "method": "GET",
        "path": "/audience-summary",
        "required_fields": ["total_comments", "genuine_comments", "sentiment_stats", "topics", "audience_summary"]
    }
}


def print_result(name: str, response: requests.Response, payload: dict):
    print("\n===", name, "===")
    print("URL:", response.url)
    print("Status code:", response.status_code)
    print("Response:")
    print(json.dumps(payload, indent=2) if payload is not None else response.text)

    if response.status_code != 200:
        print("FAIL: expected HTTP 200")
        return False

    return True


def validate_payload(name: str, payload: dict, required_fields: list) -> bool:
    missing = [field for field in required_fields if field not in payload]
    if missing:
        print(f"FAIL: missing required fields for {name}: {missing}")
        return False

    print(f"PASS: all required fields present for {name}")
    return True


def call_endpoint(name: str, spec: dict) -> bool:
    url = BASE_URL + spec["path"]
    try:
        if spec["method"] == "GET":
            response = requests.get(url, params=spec.get("params", {}), timeout=30)
        else:
            response = requests.post(url, json=spec.get("json", {}), timeout=30)

    except requests.RequestException as exc:
        print(f"FAIL: request failed for {name}: {exc}")
        return False

    try:
        payload = response.json()
    except ValueError:
        print(f"FAIL: {name} response is not valid JSON")
        print(response.text)
        return False

    is_valid = print_result(name, response, payload) and validate_payload(name, payload, spec["required_fields"])

    if is_valid and name == "analyze":
        validate_analyze_response(payload)
    if is_valid and name == "topics":
        validate_topics_response(payload)
    if is_valid and name == "audience_summary":
        validate_audience_summary_response(payload)

    return is_valid


def validate_analyze_response(payload: dict):
    print("Validating analyze response details...")
    if payload.get("total_comments", 0) < payload.get("valid_comments", 0):
        print("FAIL: valid_comments cannot exceed total_comments")
        return False
    if payload.get("spam_comments", 0) + payload.get("valid_comments", 0) != payload.get("total_comments", 0):
        print("FAIL: spam_comments + valid_comments must equal total_comments")
        return False
    print("PASS: analyze response validated")
    return True


def validate_topics_response(payload: dict):
    print("Validating topics response details...")
    if not isinstance(payload.get("topics", []), list):
        print("FAIL: topics must be a list")
        return False
    if not isinstance(payload.get("top_keywords", []), list):
        print("FAIL: top_keywords must be a list")
        return False
    if not isinstance(payload.get("wordcloud", {}), dict):
        print("FAIL: wordcloud must be a dict")
        return False
    print("PASS: topics response validated")
    return True


def validate_audience_summary_response(payload: dict):
    print("Validating audience summary response details...")
    if not payload.get("audience_summary"):
        print("FAIL: audience_summary must be present")
        return False
    if not isinstance(payload.get("sentiment_stats", {}), dict):
        print("FAIL: sentiment_stats must be a dict")
        return False
    print("PASS: audience summary response validated")
    return True


def main():
    print("Base URL:", BASE_URL)
    all_passed = True

    for name, spec in ENDPOINTS.items():
        passed = call_endpoint(name, spec)
        all_passed = all_passed and passed

    print("\n=== Summary ===")
    print("All tests passed" if all_passed else "Some tests failed")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
