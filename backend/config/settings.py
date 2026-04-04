"""
config/settings.py
------------------
Application-level settings.
All values are read from environment variables (loaded from .env).
"""

import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY: str = os.environ["GOOGLE_API_KEY"]

APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")