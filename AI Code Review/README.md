# AI Code Review System

An automated, AI-powered platform that analyzes GitHub pull requests to detect bugs, security vulnerabilities, and code quality issues. It validates findings against code evidence and generates comprehensive review reports in multiple formats.

---

## Features

-   **Automated PR Ingestion**: Seamlessly integrates with GitHub via webhooks to automatically trigger reviews on new pull requests.
-   **Diff Extraction**: Downloads and parses pull request diffs to analyze only the changed code.
-   **AI-Powered Review**: Leverages Large Language Models (LLMs) to perform deep code analysis, identifying a wide range of potential issues.
-   **Review Normalization**: Standardizes the raw output from the AI into a structured format for consistent processing.
-   **Finding Parsing**: Extracts key details from each finding, including title, file, line number, description, and recommendation.
-   **Evidence Validation**: Cross-references findings against the actual code diff to ensure they are valid and relevant.
-   **Security Scanning**: Includes a dedicated security scanner to identify common vulnerabilities and weaknesses.
-   **Severity & Confidence Classification**: Automatically assigns a severity level (e.g., Critical, High, Medium) and a confidence score to each finding.
-   **Duplicate Finding Removal**: Employs a deduplication engine to filter out redundant findings, ensuring reports are concise and actionable.
-   **Statistics Generation**: Calculates and summarizes key metrics, such as findings per file and severity distribution.
-   **Multi-Format Reporting**: Generates professional reports in Markdown, HTML, and plain text formats.
-   **Email Notifications**: Delivers review reports directly to stakeholders via email upon completion.
-   **Review Comment Generation**: Creates pre-formatted review comments, ready to be posted on GitHub.

---

## Architecture

The system is designed as a sequential pipeline that processes pull requests through various stages of analysis and reporting.

#### Workflow Diagram

```
GitHub Pull Request
       │
       ↓
 Webhook Server
       │
       ↓
 Diff Extraction
       │
       ↓
   AI Reviewer
       │
       ↓
Review Normalization
       │
       ↓
  Finding Parser
       │
       ↓
Evidence Validator
       │
       ↓
 Security Scanner
       │
       ↓
   Deduplication
       │
       ↓
Severity & Confidence Classification
       │
       ↓
  Report Builder
       │
       ↓
Markdown / HTML Reports
       │
       ↓
Email Notification
```

#### Workflow Explanation

The process begins when a GitHub pull request triggers a webhook, which is received by the Flask-based `Webhook Server`. The server then extracts the code differences (`.diff` files) and passes them to the `AI Reviewer`. After the AI generates its analysis, the findings are normalized, parsed, and validated. A dedicated `Security Scanner` runs in parallel. All findings are then deduplicated and classified by severity and confidence. Finally, the `Report Builder` aggregates all data to generate Markdown and HTML reports, which are then dispatched via email.

---

## Tech Stack

-   **Backend**: Python, Flask
-   **Artificial Intelligence**: OpenAI API
-   **Version Control**: GitHub REST API
-   **Notifications**: SMTP (Python `smtplib`)
-   **Data Formats**: HTML, Markdown, JSON

---

## Project Structure

The codebase is organized into modular components to ensure separation of concerns and maintainability.

```
AI-Code-Review/
│
├── app/
│   ├── review_engine.py           # Core review orchestration
│   ├── review_parser.py           # Parses AI-generated findings
│   ├── evidence_validator.py      # Validates findings against code
│   ├── security_scanner.py        # Scans for security issues
│   ├── report_builder.py          # Constructs the final report object
│   ├── markdown_reporter.py       # Generates Markdown reports
│   ├── html_reporter.py           # Generates HTML reports
│   ├── report_statistics.py       # Calculates review metrics
│   ├── review_comment_generator.py# Creates formatted comments
│   └── ...
│
├── reports/
│   ├── review_report.md           # Example Markdown output
│   └── review_comments.txt        # Example comments artifact
│
├── reviews/                       # Stores downloaded PR diffs
│
├── webhook_server.py              # Entry point for GitHub webhooks
│
└── README.md
```

-   **`app/`**: Contains the core business logic, including the review pipeline, parsers, validators, and report generators.
-   **`reports/`**: The output directory where all generated review artifacts (Markdown, HTML, text files) are saved.
-   **`reviews/`**: A temporary storage directory for the `.diff` files downloaded from GitHub pull requests.
-   **`webhook_server.py`**: A lightweight Flask application that listens for incoming GitHub webhook events to initiate the review process.

---

## Example Output

The system produces clear, concise, and actionable feedback for developers.

```
[Critical] Division by zero

File: bad_example.py
Line: 24

Recommendation:
Validate the divisor before performing the division to prevent a ZeroDivisionError at runtime.
```

---

## Example Workflow

1.  A developer opens a new pull request in a connected GitHub repository.
2.  The `Webhook Server` receives the `pull_request` event payload.
3.  The system extracts the changed files and saves the diffs locally.
4.  The `AI Reviewer` analyzes the code patch and generates a raw review.
5.  Findings are parsed, validated against the code, and enriched with metadata.
6.  The `Security Scanner` runs to identify potential vulnerabilities.
7.  All findings are classified by severity and confidence, and duplicates are removed.
8.  Markdown, HTML, and plain-text comment reports are generated.
9.  An email notification containing the HTML report is sent to the designated recipients.

---

## Future Enhancements

-   **GitHub Inline Review Comments**: Post findings as comments directly on the corresponding lines of code in the pull request.
-   **GitHub Checks API Integration**: Use the Checks API to provide rich, integrated feedback within the GitHub UI.
-   **Multi-Language Support**: Extend analysis capabilities to other programming languages like JavaScript, Java, and Go.
-   **Historical Review Analytics**: Implement a database to store review history and provide insights into code quality trends over time.
-   **Reviewer Dashboard**: Develop a web-based dashboard for viewing past reports, configuring settings, and monitoring system status.
-   **CI/CD Integration**: Package the system as a GitHub Action or a container to allow for seamless integration into existing CI/CD pipelines.

---

## Author

-   **Name**: [Your Name]
-   **GitHub**: [Your GitHub Profile URL]
-   **LinkedIn**: [Your LinkedIn Profile URL]
