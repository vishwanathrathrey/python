def generate_markdown(report):

    critical = 0
    warning = 0
    suggestion = 0

    category_counts = {
        "bugs": 0,
        "security": 0,
        "quality": 0
    }

    reviewed_files = set()

    for finding in report.findings:

        reviewed_files.add(finding.filename)

        category_counts[finding.category] += 1

        if finding.severity == "Critical":
            critical += 1

        elif finding.severity == "Warning":
            warning += 1

        elif finding.severity == "Suggestion":
            suggestion += 1

    markdown = "# AI Code Review Report\n\n"

    markdown += "## Summary\n\n"
    markdown += f"Files Reviewed: {len(reviewed_files)}\n"
    markdown += f"Critical: {critical}\n"
    markdown += f"Warning: {warning}\n"
    markdown += f"Suggestion: {suggestion}\n\n"

    markdown += "## By Category\n\n"
    markdown += f"Bugs: {category_counts['bugs']}\n"
    markdown += f"Security: {category_counts['security']}\n"
    markdown += f"Quality: {category_counts['quality']}\n\n"

    markdown += "## Findings\n\n"

    if not report.findings:
        markdown += "No findings detected.\n"
        return markdown

    for finding in report.findings:

        markdown += (
                        f"- [{finding.severity}] "
                        f"[{finding.confidence} Confidence] "
                        f"{finding.filename} "
                        f"{finding.description} "
                        f"(Line {finding.line})\n"
                    )

    return markdown