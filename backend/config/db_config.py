"""
config/db_config.py
-------------------
PostgreSQL connection config.
All values are read from environment variables (loaded from .env).
Nothing is hard-coded here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG: dict = {
    "host":     os.environ["POSTGRES_HOST"],
    "port":     os.environ["POSTGRES_PORT"],
    "dbname":   os.environ["POSTGRES_DB"],
    "user":     os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
}