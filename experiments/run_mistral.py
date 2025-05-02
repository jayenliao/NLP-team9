import os
from mistralai import Mistral
from dotenv import load_dotenv

try:
    from .utils import load_api_keys
except ImportError:
    from utils import load_api_keys

def test_mistral_connection():
    """Tests Mistral API connectivity."""
    print("\nTesting Mistral API...")

    # Load API key
    _, mistral_api_key = load_api_keys()
    if not mistral_api_key:
        print("No Mistral API key. Skipping.")
        return

    try:
        client = Mistral(api_key=mistral_api_key)

        # --- Model Recommendations ---
        # Testing: Use "mistral-small-latest" for speed/cost balance, or "ministral-8b-latest"/"ministral-3b-latest" for cheaper tests. All share free tier (1 RPS, 500k TPM, 1B Tokens/Month).
        # Experimentation: Use "mistral-large-latest" for complex reasoning, "mistral-small-latest" for balanced multimodal tasks, or "codestral-latest" for coding.
        model = "mistral-small-latest"

        messages = [{"role": "user", "content": "Yo"}]
        print(f"Sending: '{messages[0]['content']}' to '{model}'")

        response = client.chat.complete(model=model, messages=messages)
        print("\nMistral Response:", response.choices[0].message.content)
        print("Mistral test passed!")

    except Exception as e:
        print(f"\nMistral error: {e}")
        print("Mistral test failed.")

if __name__ == "__main__":
    load_dotenv()
    test_mistral_connection()