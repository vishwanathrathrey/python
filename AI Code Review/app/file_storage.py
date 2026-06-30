from pathlib import Path

def save_patch(filename: str, patch: str):
    reviews_dir = Path("reviews")
    reviews_dir.mkdir(exist_ok=True)

    safe_name = filename.replace("/", "_")

    file_path = reviews_dir / f"{safe_name}.diff"

    print(f"Saving patch to reviews/: {filename} -> {file_path}")

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(patch)

    return file_path