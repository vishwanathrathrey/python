import re

from app.models import ReviewFinding

def scan_for_secrets(diff_text, filename):
    findings = []

    secret_patterns = [
        (
            r"password\s*=\s*['\"].+['\"]",
            "Hardcoded password"
        ),
        (
            r"token\s*=\s*['\"].+['\"]",
            "Hardcoded API token"
        ),
        (
            r"secret\s*=\s*['\"].+['\"]",
            "Hardcoded secret"
        ),
        (
            r"api_key\s*=\s*['\"].+['\"]",
            "Hardcoded API key"
        ),
    ]

    lines = diff_text.splitlines()

    for index, line in enumerate(lines, start=1):

        # only scan newly added code
        if not line.startswith("+"):
            continue

        for pattern, description in secret_patterns:

            if re.search(
                pattern,
                line,
                re.IGNORECASE
            ):

                findings.append(
                    ReviewFinding(
                        category="security",
                        severity="Critical",
                        description=description,
                        recommendation=(
                            "Move secret to environment variables "
                            "or a secrets manager."
                        ),
                        line=index,
                        filename=filename
                    )
                )

    return findings