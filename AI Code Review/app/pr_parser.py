from urllib.parse import urlparse

def parse_pr_url(url):
    parts = urlparse(url).path.strip("/").split("/")

    owner = parts[0]
    repo = parts[1]
    pr_number = parts[3]

    return owner, repo, pr_number