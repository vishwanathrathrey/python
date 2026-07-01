def generate_review_comments(findings):

    comments = []

    for finding in findings:

        comment = f"""
            File: {finding.filename}
            Line: {finding.line}

            [{finding.severity}] [{finding.confidence} Confidence]

            {finding.description}

            Recommendation:
            {finding.recommendation}
            """

        comments.append(comment.strip())

    return comments