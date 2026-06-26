from app.github_client import GitHubClient

client = GitHubClient()

def get_pr(owner, repo, pr_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    return client.get(url)