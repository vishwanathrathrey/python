from app.review_engine import get_diff_files, review_file
from app.report_builder import build_report
from app.markdown_reporter import generate_markdown
from app.report_writer import save_report
from app.html_reporter import generate_html_report
from app.review_scope import should_review_diff_file


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

    report = build_report(all_findings)

    markdown = generate_markdown(report)

    html = generate_html_report(report)

    save_report(
        markdown,
        "reports/review_report.md"
    )

    return report, html