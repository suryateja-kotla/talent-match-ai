import logging
import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 1. Load env before anything else
load_dotenv()

# 2. Add the backend root to sys.path so agents/ and mcp/ can be found
# This is critical for Multi-Agent imports!
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.settings import APP_HOST, APP_PORT, LOG_LEVEL
from schema.db_schema import create_database_if_not_exists, init_db
from api.resume_routes import router as resume_router

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
    description="Multi-Agent AI Recruitment System.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
# Note: As you add Application or Job Match agents, you'll add their routers here.
app.include_router(resume_router)

# ─── Startup ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    logger.info("ResumeIQ Multi-Agent Backend starting up...")
    try:
        create_database_if_not_exists()
        init_db()
        logger.info("Infrastructure & Database ready.")
    except Exception:
        logger.exception("Startup failed.")
        sys.exit(1)

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "ResumeIQ Multi-Agent API"}

# ─── Run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower(),
    )