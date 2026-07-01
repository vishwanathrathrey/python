def save_review_comments(comments):

    with open(
        "reports/review_comments.txt",
        "w",
        encoding="utf-8"
    ) as file:

        for comment in comments:

            file.write(comment)
            file.write("\n")
            file.write("-" * 80)
            file.write("\n")