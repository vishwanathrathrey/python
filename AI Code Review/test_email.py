from app.email_service import send_report_email

send_report_email(
    "vishwanathathrey@gmail.com",
    """
AI Code Review Report

Critical: 1
Warning: 2
Suggestion: 3
"""
)

print("Email sent.")