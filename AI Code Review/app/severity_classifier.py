def classify_severity(category, description):

    text = description.lower()

    if category == "security":

        critical_keywords = [
            "token",
            "password",
            "secret",
            "credential",
            "api key",
            "hardcoded"
        ]

        warning_keywords = [
            "sql injection",
            "command injection",
            "path traversal",
            "unsafe deserialization",
            "eval"
        ]

        if any(k in text for k in critical_keywords):
            return "Critical"

        if any(k in text for k in warning_keywords):
            return "Warning"

        return "Warning"

    if category == "bugs":

        critical_bug_keywords = [
            "division by zero",
            "null pointer",
            "crash",
            "exception",
            "index out of range"
        ]

        if any(k in text for k in critical_bug_keywords):
            return "Critical"

        return "Warning"

    return "Suggestion"


def classify_confidence(category, description):

    text = description.lower()

    high_confidence_keywords = [
        "password",
        "token",
        "secret",
        "credential",
        "api key",
        "hardcoded",
        "division by zero",
        "eval",
        "sql injection"
    ]

    if any(keyword in text for keyword in high_confidence_keywords):
        return "High"

    if category == "quality":
        return "Low"

    return "Medium"