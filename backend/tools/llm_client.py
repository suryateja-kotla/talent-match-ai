import google.generativeai as genai
from config.settings import GOOGLE_API_KEY

def get_gemini_model(system_instruction: str):
    genai.configure(api_key=GOOGLE_API_KEY)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction
    )