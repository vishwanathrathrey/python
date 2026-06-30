from pathlib import Path


def get_pr_file_exclusion_reason(filename: str):
    path = Path(filename)

    if any(part in {"reviews", "reports"} for part in path.parts):
        return "generated-artifact-directory"

    if path.suffix != ".py":
        return "non-python-file"

    if path.name.startswith("test_"):
        return "test-file"

    return None


def should_review_pr_file(filename: str) -> bool:
    return get_pr_file_exclusion_reason(filename) is None


def get_diff_file_exclusion_reason(diff_path: str):
    path = Path(diff_path)
    name = path.name

    if not name.endswith(".diff"):
        return "not-a-diff"

    if name.endswith(".diff.diff"):
        return "generated-artifact-diff"

    if "reviews_" in name or "reports_" in name:
        return "generated-artifact-diff"

    if name.endswith(".py.diff") and "test_" in name:
        return "test-file"

    return None


def should_review_diff_file(diff_path: str) -> bool:
    return get_diff_file_exclusion_reason(diff_path) is None
