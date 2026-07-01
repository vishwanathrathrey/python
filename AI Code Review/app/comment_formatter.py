def build_pr_review_comment(findings):

    lines = []

    lines.append("## AI Code Review")

    for finding in findings:

        lines.append(
            f"- **{finding.severity}** "
            f"({finding.confidence}) "
            f"{finding.description}"
        )

    return "\n".join(lines)