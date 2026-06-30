# AI Code Review Report

## Summary

Critical: 0
Warning: 3
Suggestion: 3

## Findings

- [Warning] AI Code Review_app_bad_example.py.diff Hardcoded API token in source code (Line 4)
- [Warning] AI Code Review_app_bad_example.py.diff Hardcoded password in source code (Line 12)
- [Suggestion] AI Code Review_app_diff_loader.py.diff Function 'load_patch' is not documented (Line 4)
- [Suggestion] AI Code Review_app_json_utils.py.diff The function `extract_json` uses the `strip()` method multiple times, which can lead to performance issues. (Line 5)
- [Warning] AI Code Review_app_ollama_client.py.diff Insecure HTTP request without SSL/TLS (Line 12)
- [Suggestion] AI Code Review_app_severity_classifier.py.diff The function `classify_severity` has a docstring that is not formatted. (Line 2)
