from flask import Flask, request
from app.pr_service import get_changed_files
from app.file_storage import save_patch
from app.report_service import generate_review_report
from app.user_registry import get_user_email
from app.email_service import send_report_email
from app.review_scope import get_pr_file_exclusion_reason, should_review_pr_file
from app.comment_formatter import build_pr_review_comment
from app.github_review_poster import post_review_comment
import os

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <html>
        <head>
            <title>AI Code Review</title>
        </head>
        <body>
            <h1>AI Code Review Webhook Running</h1>
        </body>
    </html>
    """


@app.route("/webhook", methods=["POST"])
def webhook():

    payload = request.json

    action = payload.get("action")

    if action not in [
        "opened",
        "synchronize"
    ]:
        print(
            f"Ignoring action: {action}"
        )

        return {
            "status": "ignored"
        }, 200

    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})

    author = pr.get("user", {}).get("login")
    pr_number = pr.get("number")
    repo_name = repo.get("full_name")
    owner, repo_name_only = repo_name.split("/")

    print("\n========== GITHUB EVENT ==========")
    print("Action:", action)
    print("Repository:", repo_name)
    print("Author:", author)
    print("Owner:", owner)
    print("Repo:", repo_name_only)
    print("PR Number:", pr_number)

    changed_files = get_changed_files(
    owner,
    repo_name_only,
    pr_number
    )

    print(
        f"Changed Files: {len(changed_files)}"
    )

    saved_diff_paths = []

    for file in changed_files:

        if not file.patch:
            print(f"Skipping {file.filename}: empty patch")
            continue

        reason = get_pr_file_exclusion_reason(file.filename)

        if reason is not None:
            print(f"Skipping {file.filename}: {reason}")
            continue

        if not should_review_pr_file(file.filename):
            print(f"Skipping {file.filename}: not reviewable")
            continue

        path = save_patch(
            file.filename,
            file.patch
        )

        saved_diff_paths.append(path)

        print(f"Saved review diff: {path}")
    
    print(f"Saved {len(saved_diff_paths)} review diffs for this webhook run")

    report, html = generate_review_report(saved_diff_paths)

    review_comment = build_pr_review_comment(report.findings)

    github_token = os.getenv("GITHUB_TOKEN")
    if github_token and report.findings:
        status = post_review_comment(
            owner,
            repo_name_only,
            pr_number,
            github_token,
            review_comment
        )
        print(f"GitHub review comment status: {status}")
        
    email = get_user_email(author)

    if email:

        send_report_email(
            email,
            html
        )

        print(
            f"Report emailed to {email}"
        )

    else:

        print(
            f"No email found for {author}"
        )

    return {
        "status": "received"
    }, 200  

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )