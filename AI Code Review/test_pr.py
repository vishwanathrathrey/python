from app.pr_service import get_pr

pr = get_pr("microsoft", "vscode", "123")

print(pr["title"])