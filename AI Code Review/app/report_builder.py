from app.models import ReviewReport

def build_report(findings):
    return ReviewReport(findings=findings)