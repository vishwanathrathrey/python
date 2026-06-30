from pathlib import Path

def load_patch(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()