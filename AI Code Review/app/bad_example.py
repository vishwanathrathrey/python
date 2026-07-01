import os

API_TOKEN = "ghp_123456789abcdef"  # hardcoded secret


def divide(a, b):
    return a / b


def run_expression(user_input):
    return eval(user_input)


def get_user_data(user_id):

    password = "admin123"  # hardcoded password

    url = (
        "https://api.example.com/users/"
        + user_id
    )

    return {
        "password": password,
        "token": API_TOKEN,
        "url": url
    }


result = divide(10, 0)

print(result)

print(
    run_expression(
        "2 + 2"
    )
)