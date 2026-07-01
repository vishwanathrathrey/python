import re


GENERIC_PHRASES = [
    "missing docstring",
    "code can be improved",
    "code could be improved",
    "readability issue",
    "maintainability concern",
    "best practice",
    "consider using",
    "could be better",
    "should be improved",
]

CREDENTIAL_KEYWORDS = [
    "password",
    "passwd",
    "passphrase",
    "token",
    "api token",
    "api_key",
    "api key",
    "secret",
    "credential",
]

RISKY_CALL_PATTERN = re.compile(
    r"\b(open|requests\.[A-Za-z_]+|client\.get|subprocess\.[A-Za-z_]+|json\.loads|pickle\.load|yaml\.load|execute\()",
    re.IGNORECASE,
)

HUNK_HEADER_PATTERN = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _is_generic_description(description: str) -> bool:
    normalized = _normalize(description)

    if not normalized:
        return True

    return any(phrase in normalized for phrase in GENERIC_PHRASES)


def _parse_diff_lines(diff_content: str):
    line_map = {}
    ordered_lines = []

    current_old_line = None
    current_new_line = None
    in_hunk = False

    for raw_line in (diff_content or "").splitlines():
        hunk_match = HUNK_HEADER_PATTERN.match(raw_line)

        if hunk_match:
            current_old_line = int(hunk_match.group("old_start"))
            current_new_line = int(hunk_match.group("new_start"))
            in_hunk = True
            continue

        if not in_hunk:
            continue

        if raw_line.startswith("+++") or raw_line.startswith("---"):
            continue

        if not raw_line:
            continue

        prefix = raw_line[0]
        text = raw_line[1:] if prefix in {"+", "-", " "} else raw_line

        if prefix == "+":
            line_number = current_new_line
            current_new_line += 1
        elif prefix == "-":
            line_number = current_old_line
            current_old_line += 1
        else:
            line_number = current_new_line
            current_new_line += 1
            current_old_line += 1

        if line_number is None:
            continue

        line_map.setdefault(line_number, []).append(text)
        ordered_lines.append((line_number, text))

    return line_map, ordered_lines


def _line_text(line_map, line_number: int) -> str:
    return "\n".join(line_map.get(line_number, []))


def _has_matching_credential_evidence(description: str, line_text: str) -> bool:
    description = _normalize(description)
    line_text = _normalize(line_text)

    if not any(keyword in description for keyword in CREDENTIAL_KEYWORDS):
        return False

    if not any(
        marker in line_text
        for marker in [
            "password",
            "passwd",
            "token",
            "secret",
            "credential",
            "api_key",
            "api key",
        ]
    ):
        return False

    return bool(re.search(r"=\s*['\"].+['\"]", line_text))


def _has_eval_evidence(description: str, line_text: str) -> bool:
    description = _normalize(description)
    line_text = _normalize(line_text)

    return "eval" in description and "eval(" in line_text


def _has_division_by_zero_evidence(description: str, line_text: str) -> bool:
    description = _normalize(description)
    line_text = _normalize(line_text)

    if "division by zero" not in description and "divide by zero" not in description:
        return False

    if re.search(r"(/|//|%)\s*0\b", line_text):
        return True

    if re.search(r"\(\s*[^,]+,\s*0\s*\)", line_text):
        return True

    return False


def _has_sql_injection_evidence(description: str, line_text: str) -> bool:
    description = _normalize(description)
    line_text = _normalize(line_text)

    if "sql injection" not in description:
        return False

    has_sql_keyword = any(
        keyword in line_text
        for keyword in ["select", "insert", "update", "delete", "where", "from", "execute("]
    )
    has_dynamic_sql = any(
        token in line_text
        for token in ["f\"", "f'", " + ", ".format(", "format(", "{"]
    )

    return has_sql_keyword and has_dynamic_sql


def _has_exception_handling_evidence(description: str, line_number: int, line_map, ordered_lines) -> bool:
    description = _normalize(description)

    if "exception handling" not in description and "try/except" not in description and "try except" not in description:
        return False

    line_text = _line_text(line_map, line_number)
    print("\nDEBUG VALIDATION")
    print("Description:", description)
    print("Line Number:", line_number)
    print("Line Text:", line_text)
    if not line_text:
        return False

    if not RISKY_CALL_PATTERN.search(line_text):
        return False

    nearby_lines = [
        text
        for nearby_line_number, text in ordered_lines
        if abs(nearby_line_number - line_number) <= 2
    ]

    nearby_context = "\n".join(nearby_lines).lower()

    return "try:" not in nearby_context and "except" not in nearby_context


def get_evidence_validation_reason(description: str, line, diff_content: str):
    if _is_generic_description(description):
        return "No evidence found"

    try:
        line_number = int(line)
    except (TypeError, ValueError):
        return "No evidence found"

    if line_number <= 0:
        return "No evidence found"

    line_map, ordered_lines = _parse_diff_lines(diff_content)
    
    # Check the exact line first
    line_text = _line_text(line_map, line_number)
    print("\nDEBUG VALIDATION")
    print("Description:", description)
    print("Line Number:", line_number)
    print("Line Text:", line_text)
    
    # If the exact line is blank, check nearby lines (AI may report wrong line number)
    if not line_text:
        for offset in [1, 2, 3, -1, -2, -3]:
            nearby_line = line_number + offset
            line_text = _line_text(line_map, nearby_line)
            if line_text:
                line_number = nearby_line
                break
    
    # If still no content found, reject
    if not line_text:
        return "No evidence found"

    if _has_matching_credential_evidence(description, line_text):
        return None
    
    if _has_hardcoded_secret_evidence(description, line_text):
        return None

    if _has_eval_evidence(description, line_text):
        return None

    if _has_division_by_zero_evidence(description, line_text):
        return None

    if _has_sql_injection_evidence(description, line_text):
        return None

    if _has_exception_handling_evidence(description, line_number, line_map, ordered_lines):
        return None
    
    if _has_naming_evidence(description, line_text):
        return None

    return "No evidence found"


def validate_finding_evidence(description: str, line, diff_content: str) -> bool:
    return get_evidence_validation_reason(description, line, diff_content) is None

def _has_hardcoded_secret_evidence(description: str, line_text: str) -> bool:

    description = _normalize(description)
    line_text = _normalize(line_text)

    keywords = [
        "hardcoded",
        "token",
        "password",
        "secret",
        "credential",
        "api key"
    ]

    if not any(word in description for word in keywords):
        return False

    return bool(re.search(r"=\s*['\"].+['\"]", line_text))

def _has_naming_evidence(description: str, line_text: str) -> bool:

    description = _normalize(description)

    keywords = [
        "function name",
        "parameter",
        "variable name",
        "too short"
    ]

    if not any(word in description for word in keywords):
        return False

    return bool(
        re.search(
            r"def\s+[a-z]{1,2}\(",
            line_text
        )
    )