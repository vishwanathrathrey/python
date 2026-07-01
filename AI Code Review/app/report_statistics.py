from collections import defaultdict, Counter


def summarize_by_file(findings):

    stats = defaultdict(list)

    for finding in findings:
        stats[finding.filename].append(finding)

    return stats


def summarize_counts(findings):

    severity_counts = Counter()
    category_counts = Counter()

    for finding in findings:

        severity_counts[finding.severity] += 1
        category_counts[finding.category] += 1

    return {
        "severity": dict(severity_counts),
        "category": dict(category_counts)
    }