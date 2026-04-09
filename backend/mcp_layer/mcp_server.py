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
    Fetch jobs filtered by location.
    """

    try:
        rows = db_schema.list_jobs_by_location(location)

        jobs = []

        for job in rows:
            jobs.append({
                "job_id": job.get("id"),
                "title": job.get("job_title"),
                "required_skills": job.get("required_skills") or [],
                "experience_years": job.get("experience_years", 0),
                "description": job.get("job_description"),
                "location": job.get("location"),
            })

        return json.dumps(jobs)

    except Exception:
        logger.exception("get_jobs_by_location failed")
        return json.dumps([])
    
# mcp_layer/mcp_server.py — replace save_job tool

@mcp.tool()
def get_candidate_by_id(candidate_id: int) -> str:
    try:
        record = db_schema.get_candidate_by_id(candidate_id)
        if record is None:
            return json.dumps({
                "success": False,
                "data": None,
                "message": "Candidate not found"
            })

        return json.dumps({
            "success": True,
            "data": record
        })

    except Exception as exc:
        logger.exception("get_candidate_by_id failed")
        return json.dumps({
            "success": False,
            "data": None,
            "message": str(exc)
        })
        
        
@mcp.tool()
def save_job(job_json: str | dict) -> str:
    """Save a job description into the database."""
    try:
        raw = json.loads(job_json) if isinstance(job_json, str) else job_json

        normalized = {
            "job_title":          raw.get("job_title", ""),
            "location":           raw.get("location", ""),
            "experience_years":   raw.get("experience_years")
                                  or raw.get("experience_required", 0),
            "required_skills":    raw.get("required_skills")
                                  or raw.get("skills_required", []),
            "job_description":    raw.get("job_description", ""),
            "number_of_positions": raw.get("number_of_positions", 1),
        }

        job_id = db_schema.insert_job(normalized)

        return json.dumps({
            "success": True,
            "job_id": job_id,
            "message": f"Job '{normalized['job_title']}' saved successfully with ID {job_id}.",
        })

    except Exception as exc:
        logger.error("save_job failed: %s", exc)
        return json.dumps({
            "success": False,
            "job_id": None,
            "message": str(exc),
        })
@mcp.tool()
def map_candidate_to_job(candidate_id: int, job_id: int) -> str:
    """Map a candidate to a job with a calculated match score."""
    try:
        # get candidate
        candidate = db_schema.get_candidate_by_email  # you may need get by id
        # you might need to create get_candidate_by_id()

        # get job
        jobs = db_schema.list_jobs()
        job = next((j for j in jobs if j["id"] == job_id), None)

        if not job:
            return json.dumps({"success": False, "message": "Job not found"})

        # TEMP LOGIC (simple match)
        candidate_skills = []  # fetch from candidate
        job_skills = job.get("required_skills", [])

        match_score = len(set(candidate_skills) & set(job_skills))

        db_schema.create_application(candidate_id, job_id, match_score)

        return json.dumps({
            "success": True,
            "match_score": match_score
        })

    except Exception as exc:
        logger.error("mapping failed: %s", exc)
        return json.dumps({
            "success": False,
            "message": str(exc)
        })
# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("ResumeIQ MCP Server starting (stdio transport)…")
    mcp.run(transport="stdio")
