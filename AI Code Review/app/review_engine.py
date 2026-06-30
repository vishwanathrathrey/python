from pathlib import Path

from app.diff_loader import load_patch
from app.evidence_validator import get_evidence_validation_reason
from app.review_normalizer import normalize_review
from app.reviewer import review_patch
from app.review_parser import parse_review
from app.json_utils import extract_json


def get_diff_files():
    return list(Path("reviews").glob("*.diff"))


def review_file(diff_path):
    print(f"Sending to AI reviewer: {diff_path}")

    patch = load_patch(diff_path)

    result = review_patch(patch)

    clean_json = extract_json(result)

    review = normalize_review(clean_json)

    findings = parse_review(review)

    validated_findings = []

    for finding in findings:
        reason = get_evidence_validation_reason(
            finding.description,
            finding.line,
            patch
        )

        if reason is None:
            finding.filename = Path(diff_path).name
            print(f"[VALIDATED] {finding.description} (Line {finding.line})")
            validated_findings.append(finding)
        else:
            print(f"[REJECTED] {finding.description} ({reason})")

    return validated_findings