import json

EMPTY_REVIEW = {
    "bugs": [],
    "security": [],
    "quality": []
}


def normalize_review(raw_json):

    try:
        review = json.loads(raw_json)

    except json.JSONDecodeError:
        return EMPTY_REVIEW.copy()

    if isinstance(review, list):
        return EMPTY_REVIEW.copy()

    if review == {}:
        return EMPTY_REVIEW.copy()

    review.setdefault("bugs", [])
    review.setdefault("security", [])
    review.setdefault("quality", [])

    return review