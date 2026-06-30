from app.file_storage import save_patch
from app.pr_parser import parse_pr_url
from app.pr_service import get_changed_files, get_pr_files
from app.models import ChangedFile

url = "https://github.com/vishwanathrathrey/python/pull/1"

owner, repo, pr_number = parse_pr_url(url)

changed_files = get_changed_files(owner, repo, pr_number)

for file in changed_files:
    path = save_patch(
        file.filename,
        file.patch
    )

    print(f"Saved: {path}")