import requests
import json

ENABLE_GITHUB_COMMENTS = False

def post_review_comment(
    owner,
    repo,
    pull_number,
    token,
    commit_id,
    path,
    line,
    body
):
    """
    Posts a review comment to a GitHub pull request.
    """
    if not ENABLE_GITHUB_COMMENTS:
        print("GitHub review comment publishing disabled")
        return 201  # Return a success-like status to not break the pipeline

    url = (
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/comments"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    payload = {
        "body": body,
        "commit_id": commit_id,
        "path": path,
        "line": line
    }

    print(f"Posting review comment to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print(f"GitHub review comment status: {response.status_code}")
    if response.status_code != 201:
        print(f"GitHub review comment response: {response.text}")

    return response.status_code