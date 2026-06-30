import os
import  resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")


def send_report_email(recipient, report_html):

    response = resend.Emails.send({
        "from": "aireviewer@resend.dev",
        "to": recipient,
        "subject": "AI Code Review Report",
        "html": report_html
    })

    return response