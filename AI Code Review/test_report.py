import unittest
from app.models import ReviewFinding
from app.report_builder import build_report

class TestReportBuilder(unittest.TestCase):
    def test_build_report(self):
        findings = [
            ReviewFinding(
                category="quality",
                severity="Suggestion",
                description="Add timeout",
                recommendation="Add a timeout",
                filename="app/client.py",
                line=16
            )
        ]

        report = build_report(findings)
        self.assertEqual(len(report.findings), 1)
        self.assertIn("app/client.py", report.file_summary)

if __name__ == '__main__':
    unittest.main()
