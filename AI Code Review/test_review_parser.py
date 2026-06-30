import json
from app.json_utils import extract_json
from app.diff_loader import load_patch
from app.reviewer import review_patch
from app.review_parser import parse_review

patch = load_patch(
    "reviews/AI Code Review_app_github_client.py.diff"
)

result = review_patch(patch)
# print("RAW RESPONSE:")
# print(result)

clean_json = extract_json(result)

review = json.loads(clean_json)

findings = parse_review(review)
print("Number of findings:", len(findings))
for finding in findings:
    print(f"Category : {finding.category}")
    print(f"Severity : {finding.severity}")
    print(f"Line     : {finding.line}")
    print(f"Issue    : {finding.description}")
    print()