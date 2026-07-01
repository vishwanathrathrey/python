def is_valid_finding(description: str):

    description = description.lower().strip()

    invalid_phrases = [
        "no issues found",
        "no quality issues found",
        "no security issues found",
        "no bugs found",

        # common hallucinations
        "hardcoded environment variable",
        "missing a docstring",
        "code is empty",
        "file not opened in append mode"
    ]

    vague_phrases = [
        "can be improved",
        "better readability",
        "maintainability"
    ]

    # reject known bad findings
    if any(
        phrase in description
        for phrase in invalid_phrases
    ):
        return False

    # reject vague findings
    if any(
        phrase in description
        for phrase in vague_phrases
    ):
        return False

    return True

def is_valid_finding(description: str):


    description = description.lower().strip()

    invalid_phrases = [
        "no issues found",
        "no quality issues found",
        "no security issues found",
        "no bugs found",

        # common hallucinations
        "hardcoded environment variable",
        "missing a docstring",
        "code is empty",
        "file not opened in append mode"
    ]

    vague_phrases = [
        "can be improved",
        "better readability",
        "maintainability"
    ]

    if any(
        phrase in description
        for phrase in invalid_phrases
    ):
        return False

    if any(
        phrase in description
        for phrase in vague_phrases
    ):
        return False

    return True


def remove_duplicate_findings(findings):

    seen = set()
    unique = []

    for finding in findings:

        key = (
            finding.filename,
            finding.line,
            finding.description.lower()
        )

        if key not in seen:
            seen.add(key)
            unique.append(finding)

    return unique