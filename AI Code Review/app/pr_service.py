from app.github_client import GitHubClient
from app.models import ChangedFile
from app.github_client import GitHubClient

client = GitHubClient()

def get_pr(owner, repo, pr_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

def get_pr_files(owner, repo, pr_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    files = client.get(url)

    print(f"GitHub returned {len(files)} changed files")

    for file in files:
        print(f"GitHub file: {file.get('filename')}")

    return files

def get_changed_files(owner, repo, pr_number):
    files = get_pr_files(owner, repo, pr_number)

    changed_files = []

    for file in files:
        changed_files.append(
            ChangedFile(
                filename=file["filename"],
                status=file["status"],
                patch=file.get("patch", "")
            )
        )

    return changed_files

def get_pr_author(owner, repo, pr_number):

    client = GitHubClient()

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/pulls/{pr_number}"
    )

    pr_data = client.get(url)

    return pr_data["user"]["login"]