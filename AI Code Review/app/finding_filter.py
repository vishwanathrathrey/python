def is_valid_finding(description: str):
    description = description.lower()

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

    # reject extremely short findings
    if len(description.split()) < 5:
        return False

    return True