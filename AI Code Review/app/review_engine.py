from pathlib import Path

from app.diff_loader import load_patch
from app.review_normalizer import normalize_review
from app.reviewer import review_patch
from app.review_parser import parse_review
from app.json_utils import extract_json


def get_diff_files():
    return list(Path("reviews").glob("*.diff"))


def review_file(diff_path):
    patch = load_patch(diff_path)

    try:
        result = review_patch(patch)

        clean_json = extract_json(result)

        review = normalize_review(clean_json)

    except Exception as e:
        print("\n====================")
        print("FAILED FILE:", diff_path)
        print("RAW RESPONSE:")
        print(result)
        print("ERROR:", e)
        return []

    findings = parse_review(review)

    for finding in findings:
        finding.filename = Path(diff_path).name

    return findings