import unittest
from app.models import ReviewFinding, ReviewReport
from app.markdown_reporter import generate_markdown

class TestMarkdownReporter(unittest.TestCase):
    def test_generate_markdown(self):
        report = ReviewReport(
            findings=[
                ReviewFinding(
                    category="security",
                    severity="Critical",
                    description="Hardcoded API token",
                    recommendation="Move to env var",
                    filename="app/main.py",
                    line=10
                ),
                ReviewFinding(
                    category="quality",
                    severity="Suggestion",
                    description="Add timeout to requests.get()",
                    recommendation="Add a timeout",
                    filename="app/client.py",
                    line=16
                )
            ]
        )

        markdown = generate_markdown(report)
        self.assertIn("Hardcoded API token", markdown)
        self.assertIn("Add timeout to requests.get()", markdown)

if __name__ == '__main__':
    unittest.main()