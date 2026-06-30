from app.pr_parser import parse_pr_url
from app.pr_service import get_pr
from app.pr_service import get_changed_files

url = "https://github.com/vishwanathrathrey/python/pull/1"

owner, repo, pr_number = parse_pr_url(url)

pr = get_pr(owner, repo, pr_number)

print("Title:", pr["title"])
print("State:", pr["state"])
print("Author:", pr["user"]["login"])
print("Changed Files:", pr["changed_files"])
print("Additions:", pr["additions"])
print("Deletions:", pr["deletions"])

changed_files = get_changed_files(owner, repo, pr_number)

print(len(changed_files))

for file in changed_files:
    print(file.filename)