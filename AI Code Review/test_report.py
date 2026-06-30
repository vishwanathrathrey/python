from app.models import ReviewFinding
from app.report_builder import build_report

findings = [
    ReviewFinding(
        category="quality",
        severity="Suggestion",
        description="Add timeout",
        line=16
    )
]

report = build_report(findings)

print(report)
