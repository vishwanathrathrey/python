from app.pr_parser import parse_pr_url

owner, repo, pr_number = parse_pr_url(
    "https://github.com/microsoft/vscode/pull/123"
)

print(owner)
print(repo)
print(pr_number)