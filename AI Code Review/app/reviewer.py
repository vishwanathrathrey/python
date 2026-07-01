from app.ollama_client import OllamaClient

client = OllamaClient()

def review_patch(patch: str):
    prompt = f"""
You are a senior software engineer performing a pull request review.

Review ONLY the code shown in the diff.

Rules:
- Do not invent issues.
- Do not assume missing code exists.
- Report only issues visible in the diff.
- Do not report best-practice suggestions unless there is a real problem.
- If uncertain, return empty arrays.
- Every finding must reference code that exists in the diff.
- If you cannot point to a specific line in the diff, do not report the issue.
- Do not suggest hypothetical improvements.
- Do not flag code as insecure unless the vulnerability is visible in the diff.
- Do not flag code as deprecated unless the deprecated API is explicitly shown in the diff.
- Recommendations must be specific and actionable.
- Recommendations must address the reported issue.
- Report exactly one issue per finding.
- Never combine multiple issues into a single finding.
- Every finding must reference exactly one line from the diff.
- The line number must correspond to the exact line where the issue appears.
- If multiple issues exist, return multiple findings.
- If an issue spans multiple lines, choose the most relevant line.
- If you are uncertain about the exact line number, do not report the finding.
- If no bugs, security issues, or quality concerns are found, return empty arrays.

Return ONLY valid JSON.

Schema:

{{
  "bugs": [
    {{
      "description": "text",
      "line": 1,
      "recommendation": "text"
    }}
  ],
  "security": [
    {{
      "description": "text",
      "line": 1,
      "recommendation": "text"
    }}
  ],
  "quality": [
    {{
      "description": "text",
      "line": 1,
      "recommendation": "text"
    }}
  ]
}}

Examples:

Valid:
{{
  "security": [
    {{
      "description": "Hardcoded API token in source code",
      "line": 14,
      "recommendation": "Move the token to an environment variable and load it at runtime."
    }}
  ]
}}

Bad:
{{
  "security": [
    {{
      "description": "Use of hardcoded secrets (API_TOKEN and password)",
      "line": 3,
      "recommendation": "Move secrets to environment variables."
    }}
  ]
}}

Good:
{{
  "security": [
    {{
      "description": "Hardcoded API token",
      "line": 3,
      "recommendation": "Move the token to an environment variable or secret manager."
    }},
    {{
      "description": "Hardcoded password",
      "line": 11,
      "recommendation": "Move the password to a secure secret store or environment variable."
    }}
  ]
}}

Bad:
{{
  "bugs": [
    {{
      "description": "Division by zero",
      "line": 15,
      "recommendation": "Handle division by zero."
    }}
  ]
}}

Good:
{{
  "bugs": [
    {{
      "description": "Division by zero",
      "line": 24,
      "recommendation": "Validate the divisor before performing the division."
    }}
  ]
}}

Invalid:
{{
  "security": [
    {{
      "description": "This code may be insecure",
      "line": 1,
      "recommendation": "Improve security"
    }}
  ]
}}

Git Diff:

{patch}
"""

    raw_response = client.generate(prompt)

    print("RAW AI RESPONSE:")
    print(raw_response)

    return raw_response