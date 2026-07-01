from app.review_engine import get_diff_files, review_file
from app.report_builder import build_report
from app.markdown_reporter import generate_markdown
from app.report_writer import save_report
from app.html_reporter import generate_html_report
from app.review_scope import should_review_diff_file
from app.report_statistics import summarize_by_file, summarize_counts
from app.finding_filter import remove_duplicate_findings
from app.review_comment_generator import generate_review_comments
from app.comment_writer import save_review_comments

def generate_review_report(diff_paths=None):

    if diff_paths is None:
        diff_files = get_diff_files()
    else:
        diff_files = list(diff_paths)

    print(f"Review engine will process {len(diff_files)} diff files")

    all_findings = []

    for file in diff_files:

        print(f"Reviewing diff file: {file}")

        if not should_review_diff_file(str(file)):
            print(f"Skipping diff file: {file}")
            continue

        if not str(file).endswith(".py.diff"):
            continue

        findings = review_file(str(file))

        all_findings.extend(findings)

    before_count = len(all_findings)
    all_findings = remove_duplicate_findings(all_findings)
    after_count = len(all_findings)
    print(f"Deduplicated findings: "
        f"{before_count} -> {after_count}")

    report = build_report(all_findings)

    comments = generate_review_comments(report.findings)
    save_review_comments(comments)
    print("\nREVIEW COMMENTS")
    for comment in comments:
        print(comment)
        print("-" * 80)

    print("\nFILE SUMMARY")
    print(report.file_summary)
    print("\nCOUNT SUMMARY")
    print(report.count_summary)

    print("FINAL REPORT FINDINGS:")
    print(report.findings)
    print(f"FINAL REPORT FINDINGS COUNT: {len(report.findings)}")

    markdown = generate_markdown(report)

    html = generate_html_report(report)

    save_report(
        markdown,
        "reports/review_report.md"
    )

    save_report(
        html,
        "reports/review_report.html"
    )
    print("HTML report saved")

    return report, html