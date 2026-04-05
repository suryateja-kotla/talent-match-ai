"""
config/settings.py
------------------
Application-level settings.
All values are read from environment variables (loaded from .env).
"""

import os
from dotenv import load_dotenv

load_dotenv()

# GOOGLE_API_KEY: str = os.environ["GOOGLE_API_KEY"]

GCP_PROJECT_ID: str = os.environ.get("GCP_PROJECT_ID")
GCP_LOCATION: str = os.environ.get("GCP_LOCATION", "us-central1")
 
# --- VERTEX AI MAGIC TRIGGER ---
# Injecting these into os.environ tells the underlying google-genai
# SDK inside ADK to automatically route through Vertex AI using ADC.
os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = GCP_LOCATION
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")