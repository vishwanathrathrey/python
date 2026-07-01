import unittest
import os
from app.models import ReviewFinding, ReviewReport
from app.markdown_reporter import generate_markdown
from app.report_writer import save_report

class TestReportWriter(unittest.TestCase):
    def test_save_report(self):
        report = ReviewReport(
            findings=[
                ReviewFinding(
                    category="security",
                    severity="Critical",
                    description="Hardcoded API token",
                    recommendation="Move to env var",
                    filename="app/main.py",
                    line=10
                )
            ]
        )

        markdown = generate_markdown(report)
        filepath = "reports/test_review_report.md"
        save_report(markdown, filepath)

        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r") as f:
            content = f.read()
            self.assertIn("Hardcoded API token", content)

        os.remove(filepath)

if __name__ == '__main__':
    unittest.main()