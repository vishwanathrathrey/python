from app.ollama_client import OllamaClient

client = OllamaClient()

response = client.generate(
    """
Review this code and identify bugs:

def divide(a, b):
    return a / b
    """
)

print(response)