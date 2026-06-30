def classify_severity(category, description):

    text = description.lower()

    if category == "security":

        critical_keywords = [
            "token",
            "secret",
            "password",
            "credential",
            "api key",
            "hardcoded"
        ]

        if any(word in text for word in critical_keywords):
            return "Critical"

        return "Warning"

    if category == "bugs":
        return "Warning"

    return "Suggestion"