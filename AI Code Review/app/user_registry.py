import json


def get_user_email(username):

    with open("config/users.json", "r") as file:
        users = json.load(file)

    user = users.get(username)

    if not user:
        return None

    return user.get("email")