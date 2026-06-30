from app.models import ReviewFinding, ReviewReport
from app.markdown_reporter import generate_markdown

report = ReviewReport(
    findings=[
        ReviewFinding(
            category="security",
            severity="Critical",
            description="Hardcoded API token",
            line=10
        ),
        ReviewFinding(
            category="quality",
            severity="Suggestion",
            description="Add timeout to requests.get()",
            line=16
        )
    ]
)

markdown = generate_markdown(report)

print(markdown)