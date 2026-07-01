from app.models import ReviewReport
from app.report_statistics import summarize_by_file, summarize_counts


def build_report(findings):

    file_summary = summarize_by_file(findings)

    count_summary = summarize_counts(findings)

    return ReviewReport(
        findings=findings,
        file_summary=file_summary,
        count_summary=count_summary,
    )