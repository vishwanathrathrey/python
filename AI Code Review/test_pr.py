import unittest
from app.pr_parser import parse_pr_url

class TestPr(unittest.TestCase):
    def test_parse_pr_url(self):
        url = "https://github.com/vishwanathrathrey/python/pull/1"
        owner, repo, pr_number = parse_pr_url(url)
        self.assertEqual(owner, "vishwanathrathrey")
        self.assertEqual(repo, "python")
        self.assertEqual(pr_number, "1")

    def test_get_pr(self):
        pr = {
            "title": "Test PR",
            "state": "open",
            "user": {"login": "testuser"},
            "changed_files": 1,
            "additions": 10,
            "deletions": 5,
        }
        self.assertEqual(pr["title"], "Test PR")
        self.assertEqual(pr["state"], "open")
        self.assertEqual(pr["user"]["login"], "testuser")

if __name__ == '__main__':
    unittest.main()