from app.user_registry import get_user_email
from app.email_service import send_report_email

username = "vishwanathrathrey"

email = get_user_email(username)

if email:
    send_report_email(
        email,
        """
AI Code Review Report

Critical: 1
Warning: 0
Suggestion: 2
"""
    )

    print(f"Email sent to {email}")

else:
    print("User not found")