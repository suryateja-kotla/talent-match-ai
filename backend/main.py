"""
main.py
Single entry point for the ResumeIQ backend.
- Initialises the database (creates DB + tables if needed)
- Starts the FastAPI application
"""

import logging
import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import APP_HOST, APP_PORT, LOG_LEVEL
from schema.db_schema import create_database_if_not_exists, init_db
from api.resume_routes import router as resume_router


# Ensure backend root is on the path


from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ─── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="ResumeIQ API",
    description="AI-powered resume parsing and job matching system.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(resume_router)


# ─── Startup ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    logger.info("ResumeIQ starting up...")
    try:
        create_database_if_not_exists()
        init_db()
        logger.info("Database ready.")
    except Exception:
        logger.exception("Database initialisation failed. Exiting.")
        sys.exit(1)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "ResumeIQ API"}


# ─── Run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower(),
    )