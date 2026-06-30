import json

def normalize_review(raw_json):

    review = json.loads(raw_json)

    if isinstance(review, list):
        return {
            "bugs": [],
            "security": [],
            "quality": []
        }

    if review == {}:
        return {
            "bugs": [],
            "security": [],
            "quality": []
        }

    review.setdefault("bugs", [])
    review.setdefault("security", [])
    review.setdefault("quality", [])

    return review