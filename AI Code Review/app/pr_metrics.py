def calculate_metrics(findings):

    return {
        "total_findings": len(findings),
        "critical_count": len(
            [f for f in findings if f.severity == "Critical"]
        ),
        "warning_count": len(
            [f for f in findings if f.severity == "Warning"]
        ),
        "suggestion_count": len(
            [f for f in findings if f.severity == "Suggestion"]
        ),
        "high_confidence": len(
            [f for f in findings if f.confidence == "High"]
        ),
    }