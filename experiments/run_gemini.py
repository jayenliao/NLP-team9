import os
from google import genai
from dotenv import load_dotenv

try:
    from .utils import load_api_keys
except ImportError:
    from utils import load_api_keys

def test_gemini_connection():
    """Tests Gemini API connectivity."""
    print("\nTesting Gemini API...")

    # Load API key
    google_api_key, _ = load_api_keys()
    if not google_api_key:
        print("No Gemini API key. Skipping.")
        return

    try:
        client = genai.Client(api_key=google_api_key)

        # --- Model Recommendations ---
        # Testing: Use "gemini-2.0-flash-lite" (30 RPM free) or "gemini-1.5-flash"/"gemini-1.5-flash-8b" (15 RPM, 1M TPM) for cost/speed. Avoid "1.5 Pro" (2 RPM free).
        # Experimentation: Use "gemini-1.5-pro" for high reasoning, "gemini-1.5-flash" for balanced speed/capability/tuning, or "gemini-1.5-flash-8b" for cost optimization.
        model = "gemini-2.0-flash-lite"

        prompt = "Yo"
        print(f"Sending: '{prompt}' to '{model}'")

        response = client.models.generate_content(model=model, contents=prompt)
        print("\nGemini Response:", response.text)
        print("Gemini test passed!")

    except Exception as e:
        print(f"\nGemini error: {e}")
        print("Gemini test failed.")

if __name__ == "__main__":
    load_dotenv()
    test_gemini_connection()