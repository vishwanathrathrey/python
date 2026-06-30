from app.models import ReviewFinding, ReviewReport
from app.markdown_reporter import generate_markdown
from app.report_writer import save_report

report = ReviewReport(
    findings=[
        ReviewFinding(
            category="security",
            severity="Critical",
            description="Hardcoded API token",
            line=10
        )
    ]
)

markdown = generate_markdown(report)

save_report(
    markdown,
    "reports/review_report.md"
)

print("Report saved.")