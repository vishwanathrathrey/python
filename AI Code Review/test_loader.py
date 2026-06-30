from app.diff_loader import load_patch

patch = load_patch(
    "reviews/AI Code Review_app_github_client.py.diff"
)

print(patch)