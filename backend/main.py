import logging
import sys
import os
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ENV first — before any ADK/google imports
from config.settings import APP_HOST, APP_PORT, LOG_LEVEL
from schema.db_schema import create_database_if_not_exists, init_db
from api.resume_routes import router as resume_router
from api.chat import router as chat_router

load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TalentMatch + ResumeIQ API",
    description="Multi-Agent AI Recruitment System",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the routes with the main app
app.include_router(resume_router)
app.include_router(chat_router)

# ─────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────
@app.get("/")
def health_check():
    return {"status": "ok", "service": "TalentMatch + ResumeIQ API"}

# ── Startup ───────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    logger.info("Backend starting...")
    try:
        create_database_if_not_exists()
        init_db()
        logger.info(" Database ready.")
    except Exception:
        logger.exception("Startup failed")
        sys.exit(1)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower(),
    )