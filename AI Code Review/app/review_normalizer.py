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
        print("NORMALIZED REVIEW JSON:")
        print(EMPTY_REVIEW.copy())
        return EMPTY_REVIEW.copy()

    if isinstance(review, list):
        print("NORMALIZED REVIEW JSON:")
        print(EMPTY_REVIEW.copy())
        return EMPTY_REVIEW.copy()

    if review == {}:
        print("NORMALIZED REVIEW JSON:")
        print(EMPTY_REVIEW.copy())
        return EMPTY_REVIEW.copy()

    review.setdefault("bugs", [])
    review.setdefault("security", [])
    review.setdefault("quality", [])

    print("NORMALIZED REVIEW JSON:")
    print(review)

    return review