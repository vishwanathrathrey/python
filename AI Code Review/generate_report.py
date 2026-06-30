# from app.review_engine import get_diff_files, review_file
# from app.report_builder import build_report
# from app.markdown_reporter import generate_markdown
# from app.report_writer import save_report
# from app.user_registry import get_user_email
# from app.email_service import send_report_email
# from app.html_reporter import generate_html_report

# all_findings = []

# for file in get_diff_files():
#     if not str(file).endswith(".py.diff"):
#         continue
#     if "test_" in str(file):
#         continue
#     findings = review_file(str(file))
#     all_findings.extend(findings)

# report = build_report(all_findings)

# markdown = generate_markdown(report)
# html = generate_html_report(report)

# save_report(
#     markdown,
#     "reports/review_report.md"
# )
# username = "vishwanathrathrey"

# email = get_user_email(username)

# if email:
#     send_report_email(
#         email,
#         html
#     )

#     print(f"Report emailed to {email}")
# else:
#     print(
#         f"No email found for {username}"
#     )

# print("Report generated.")

from app.report_service import generate_review_report

generate_review_report()

print("Report generated.")