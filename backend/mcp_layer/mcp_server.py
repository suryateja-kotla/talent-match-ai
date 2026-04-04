import json
import logging
import os
import sys

# 1. ADD THIS FIRST: Make backend root importable when spawned as a child process
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 2. NOW import your local modules
from config.settings import LOG_LEVEL
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from schema import db_schema
from schema.pydantic_models import CandidateSchema

load_dotenv()

# Logs go to stderr so stdout stays clean for the stdio MCP wire protocol
# Logs go to stderr so stdout stays clean for the stdio MCP wire protocol
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO), # Dynamically reads from settings.py
    format="%(asctime)s [MCP-SERVER] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("mcp_debug.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

mcp = FastMCP("resumeiq-db")

# Initialize database and tables on startup
try:
    db_schema.init_db()
    logger.info("Database and schema initialized.")
except Exception as e:
    logger.error(f"FATAL: Database failed to initialize: {e}")
# ---------------------------------

# ═════════════════════════════════════════════════════════════════════════════
# MCP Tool Registry
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def save_candidate(candidate_json: str | dict) -> str:
    """Validate and upsert a candidate extracted from a resume into PostgreSQL."""
    try:
        raw = json.loads(candidate_json) if isinstance(candidate_json, str) else candidate_json
        candidate = CandidateSchema.model_validate(raw)
        candidate_id = db_schema.upsert_candidate(candidate)
        return json.dumps({
            "success": True,
            "candidate_id": candidate_id,
            "message": "Candidate saved successfully."
        })
    except Exception as exc:
        logger.error("save_candidate failed: %s", exc)
        return json.dumps({"success": False, "candidate_id": None, "message": str(exc)})

@mcp.tool()
def get_candidate_by_email(email: str) -> str:
    """Retrieve a candidate record by email address."""
    try:
        record = db_schema.get_candidate_by_email(email)
        if record is None:
            return json.dumps({"success": False, "data": None, "message": "Candidate not found."})
        return json.dumps({"success": True, "data": record, "message": "Found."})
    except Exception as exc:
        logger.exception("get_candidate_by_email: DB error")
        return json.dumps({"success": False, "data": None, "message": str(exc)})

@mcp.tool()
def list_all_candidates() -> str:
    """Return a summary list of all candidates in the database."""
    try:
        rows = db_schema.list_candidates()
        return json.dumps({"success": True, "count": len(rows), "data": rows})
    except Exception as exc:
        logger.exception("list_all_candidates: DB error")
        return json.dumps({"success": False, "count": 0, "data": [], "message": str(exc)})

@mcp.tool()
def list_all_jobs() -> str:
    """Return a list of all active job descriptions."""
    try:
        rows = db_schema.list_jobs()
        return json.dumps({"success": True, "count": len(rows), "data": rows})
    except Exception as exc:
        logger.exception("list_all_jobs: DB error")
        return json.dumps({"success": False, "count": 0, "data": [], "message": str(exc)})

@mcp.tool()
def get_jobs_by_location(location: str) -> str:
    """
    Fetch jobs (location ignored for now).
    """

    try:
        rows = db_schema.list_jobs()

        jobs = []

        for job in rows:
            jobs.append({
                "job_id": job.get("id"),
                "title": job.get("job_title"),
                "job_type": job.get("job_type"),
                "required_skills": job.get("required_skills") or [],
                "min_experience_years": job.get("min_experience_years", 0),
                "max_experience_years": job.get("max_experience_years", 0),
                "description": job.get("job_description"),
            })

        return json.dumps(jobs)

    except Exception as exc:
        logger.exception("get_jobs_by_location failed")
        return json.dumps([])
# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("ResumeIQ MCP Server starting (stdio transport)…")
    mcp.run(transport="stdio")