import os
import requests
from dotenv import load_dotenv

load_dotenv()

class GitHubClient:
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")

        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

    def get(self, url: str):
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()