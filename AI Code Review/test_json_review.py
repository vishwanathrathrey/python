from app.diff_loader import load_patch
from app.reviewer import review_patch

patch = load_patch(
    "reviews/AI Code Review_app_github_client.py.diff"
)

result = review_patch(patch)

print(result)