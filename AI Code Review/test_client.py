from app.github_client import GitHubClient

client = GitHubClient()

user = client.get("https://api.github.com/user")

print(user["login"])