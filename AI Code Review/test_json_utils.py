from app.json_utils import extract_json

sample = """
{}

Explanation:
No issues found in the diff.
"""

print(extract_json(sample))