from app.review_engine import get_diff_files
from app.review_engine import get_diff_files, review_file

files = get_diff_files()

print("Files found:", len(files))

findings = review_file(str(files[0]))

all_findings = []

for file in get_diff_files():

    print(f"Reviewing {file}")

    findings = review_file(str(file))

    all_findings.extend(findings)

print()
print("Total findings:", len(all_findings))

for finding in all_findings:
    print(finding)

