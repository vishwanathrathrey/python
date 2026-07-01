def generate_html_report(report):

    critical = 0
    warning = 0
    suggestion = 0

    for finding in report.findings:

        if finding.severity == "Critical":
            critical += 1

        elif finding.severity == "Warning":
            warning += 1

        elif finding.severity == "Suggestion":
            suggestion += 1

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">

        <h1>AI Code Review Report</h1>

        <h2>Summary</h2>

        <ul>
            <li><b>Critical:</b> {critical}</li>
            <li><b>Warning:</b> {warning}</li>
            <li><b>Suggestion:</b> {suggestion}</li>
        </ul>

        <h2>Findings</h2>

        <table border="1" cellpadding="8" cellspacing="0">

            <tr>
                <th>Severity</th>
                <th>Category</th>
                <th>Confidence</th>
                <th>File</th>
                <th>Line</th>
                <th>Description</th>
                <th>Recommendation</th>
            </tr>
    """

    for finding in report.findings:

        color = "#ffffff"

        if finding.severity == "Critical":
            color = "#ffcccc"

        elif finding.severity == "Warning":
            color = "#fff4cc"

        elif finding.severity == "Suggestion":
            color = "#ddeeff"

        html += f"""
            <tr style="background-color:{color}">
                <td>{finding.severity}</td>
                <td>{finding.category}</td>
                <td>{finding.confidence}</td>
                <td>{finding.filename}</td>
                <td>{finding.line}</td>
                <td>{finding.description}</td>
                <td>{finding.recommendation}</td>
            </tr>
        """

    html += """
        </table>

    </body>
    </html>
    """

    return html