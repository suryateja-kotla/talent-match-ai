
import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

def get_llm():
    # Use API key for authentication (not Vertex AI)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set in environment.")
    client = genai.Client(api_key=api_key)
    return client