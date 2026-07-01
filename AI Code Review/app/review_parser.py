from app.models import ReviewFinding
from app.finding_filter import is_valid_finding
from app.severity_classifier import classify_severity, classify_confidence

def parse_review(review_json):
    findings = []

    for category in ["bugs", "security", "quality"]:

        for item in review_json.get(category, []):

            description = item.get(
                "description",
                item.get("message", "")
            )

            line = int(item.get("line", item.get("line_number", 0)))

            recommendation = item.get(
                "recommendation",
                "No recommendation provided."
            )

            if not is_valid_finding(description):
                continue

            print("PARSED FINDING:")
            print(
                {
                    "category": category,
                    "description": description,
                    "line": line,
                    "recommendation": recommendation,
                }
            )

            findings.append(
                ReviewFinding(
                    category=category,
                    severity=classify_severity(
                        category,
                        description
                    ),
                    confidence=classify_confidence(
                        category,
                        description
                    ),
                    description=description,
                    recommendation=recommendation,
                    line=line,
                    filename=""
                )
            )

            print("PARSED FINDINGS LIST:")
            print(findings)

    return findings