from app.pr_parser import parse_pr_url
from app.pr_service import get_pr_author
from app.user_registry import get_user_email

url = "https://github.com/vishwanathrathrey/python/pull/1"

owner, repo, pr_number = parse_pr_url(url)

author = get_pr_author(
    owner,
    repo,
    pr_number
)

print("Author:", author)

email = get_user_email(author)

print("Email:", email)