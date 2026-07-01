import unittest
import json

class TestJsonParse(unittest.TestCase):
    def test_json_loads(self):
        result = """
{
  "findings": [
    {
      "category": "security",
      "description": "Hardcoded API token",
      "line": 10,
      "recommendation": "Move to env var"
    }
  ]
}
"""
        review = json.loads(result)
        self.assertIn("findings", review)
        self.assertEqual(len(review["findings"]), 1)

if __name__ == '__main__':
    unittest.main()