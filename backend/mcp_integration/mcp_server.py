"""
mcp/mcp_server.py
-----------------
ResumeIQ MCP Server — stdio transport.

ARCHITECTURE (matches your pg_mcp_tools reference pattern):
  • All DB helper functions live here (insert_candidate, get_candidates, etc.)
    — same pattern as your pg_mcp_tools.py but integrated directly.
  • @mcp.tool() decorators register them into the tool registry automatically.
  • FastMCP handles the tool registry, dispatch, and stdio framing.
  • The client (mcp_client.py) simply spawns this file as a child process.

Tools registered:
  save_candidate         — validate (Pydantic) + upsert into candidates table
  get_candidate_by_email — fetch one candidate by email
  list_all_candidates    — summary list of all candidates

Transport: stdio (stdout = MCP wire, stderr = logs)

Spawned by: mcp/mcp_client.py via StdioServerParameters
"""

import json
import logging
import os
import sys

# ── make backend root importable when spawned as a child process ──────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp.server.fastmcp import FastMCP

from schema.db_schema import get_connection
from schema.pydantic_models import CandidateSchema
from dotenv import load_dotenv
load_dotenv()
# Logs go to stderr so stdout stays clean for the stdio MCP wire protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP-SERVER] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("mcp_debug.log"), # <--- This will save errors to a file!
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# ── FastMCP instance (tool registry lives here) ───────────────────────────────
mcp = FastMCP("resumeiq-db")


# ═════════════════════════════════════════════════════════════════════════════
# Internal DB helper functions
# (same role as pg_mcp_tools.py in your reference — kept in one place)
# ═════════════════════════════════════════════════════════════════════════════

def _serialize(record: dict) -> dict:
    """Convert datetime fields → ISO strings so json.dumps won't fail."""
    for key in ("created_at", "updated_at", "applied_at", "status_updated_at"):
        if record.get(key):
            record[key] = str(record[key])
    return record


def _db_upsert_candidate(data: CandidateSchema) -> int:
    """
    Upsert one validated candidate into PostgreSQL.
    ON CONFLICT (email) → update all fields.
    Returns the candidate id.
    """
    sql = """
        INSERT INTO candidates (
            first_name, last_name, email, phone, linkedin_url,
            current_company, current_job_title, total_experience_years,
            skills, skill_experience, education,
            raw_text, source_file
        ) VALUES (
            %(first_name)s, %(last_name)s, %(email)s,
            %(phone)s, %(linkedin_url)s,
            %(current_company)s, %(current_job_title)s, %(total_experience_years)s,
            %(skills)s::jsonb, %(skill_experience)s::jsonb, %(education)s::jsonb,
            %(raw_text)s, %(source_file)s
        )
        ON CONFLICT (email) DO UPDATE SET
            first_name             = EXCLUDED.first_name,
            last_name              = EXCLUDED.last_name,
            phone                  = EXCLUDED.phone,
            linkedin_url           = EXCLUDED.linkedin_url,
            current_company        = EXCLUDED.current_company,
            current_job_title      = EXCLUDED.current_job_title,
            total_experience_years = EXCLUDED.total_experience_years,
            skills                 = EXCLUDED.skills,
            skill_experience       = EXCLUDED.skill_experience,
            education              = EXCLUDED.education,
            raw_text               = EXCLUDED.raw_text,
            source_file            = EXCLUDED.source_file,
            updated_at             = CURRENT_TIMESTAMP
        RETURNING id;
    """
    params = {
        "first_name":              data.first_name,
        "last_name":               data.last_name,
        "email":                   data.email,
        "phone":                   data.phone,
        "linkedin_url":            data.linkedin_url,
        "current_company":         data.current_company,
        "current_job_title":       data.current_job_title,
        "total_experience_years":  data.total_experience_years,
        # Pydantic model → JSON string → Postgres JSONB
        "skills":          json.dumps(data.skills),
        "skill_experience": json.dumps(data.skill_experience),
        "education":       json.dumps([e.model_dump() for e in data.education]),
        "raw_text":        data.raw_text,
        "source_file":     data.source_file,
    }
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            candidate_id = cur.fetchone()[0]
        conn.commit()
        logger.info("Upserted candidate id=%s  email=%s", candidate_id, data.email)
        return candidate_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _db_get_by_email(email: str) -> dict | None:
    """Return one candidate dict or None."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM candidates WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            return _serialize(dict(zip(cols, row)))
    finally:
        conn.close()


def _db_list_candidates() -> list[dict]:
    """Return summary rows for all candidates."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, first_name, last_name, email,
                       current_job_title, total_experience_years,
                       skills, source_file, created_at
                FROM   candidates
                ORDER  BY created_at DESC
            """)
            cols = [d[0] for d in cur.description]
            return [_serialize(dict(zip(cols, row))) for row in cur.fetchall()]
    finally:
        conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# MCP Tool Registry
# (@mcp.tool decorators = tool registry, same role as TOOL_REGISTRY dict
#  in your reference mcp_server.py — but FastMCP handles dispatch automatically)
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def save_candidate(candidate_json: str | dict) -> str: # Notice the updated type hint
    """Validate and upsert a candidate extracted from a resume into PostgreSQL."""
    
    # ── 1. Parse raw JSON safely ──────────────────────────────────────────────
    try:
        if isinstance(candidate_json, str):
            raw: dict = json.loads(candidate_json)
        elif isinstance(candidate_json, dict):
            raw = candidate_json # The LLM passed a dict, use it directly!
        else:
            raise ValueError(f"Expected string or dict, got {type(candidate_json)}")
            
    except Exception as exc: # Catching ALL exceptions, not just JSONDecodeError
        logger.error("save_candidate: parsing failed — %s", exc)
        return json.dumps({"success": False, "candidate_id": None,
                           "message": f"Invalid format: {exc}"})

    # ── 2. Validate with Pydantic ─────────────────────────────────────────────
    try:
        candidate = CandidateSchema.model_validate(raw)
    except Exception as exc:
        logger.error("save_candidate: validation failed — %s", exc)
        return json.dumps({"success": False, "candidate_id": None,
                           "message": f"Validation error: {exc}"})

    # ── 3. Upsert to DB ───────────────────────────────────────────────────────
    try:
        candidate_id = _db_upsert_candidate(candidate)
        return json.dumps({
            "success": True,
            "candidate_id": candidate_id,
            "message": "Candidate saved successfully.",
        })
    except Exception as exc:
        logger.exception("save_candidate: DB error")
        return json.dumps({"success": False, "candidate_id": None, "message": str(exc)})


@mcp.tool()
def get_candidate_by_email(email: str) -> str:
    """
    Retrieve a candidate record by email address.

    Args:
        email: The candidate's email.

    Returns:
        JSON string: { "success": bool, "data": dict|null, "message": str }
    """
    try:
        record = _db_get_by_email(email)
        if record is None:
            return json.dumps({"success": False, "data": None,
                               "message": "Candidate not found."})
        return json.dumps({"success": True, "data": record, "message": "Found."})
    except Exception as exc:
        logger.exception("get_candidate_by_email: DB error")
        return json.dumps({"success": False, "data": None, "message": str(exc)})


@mcp.tool()
def list_all_candidates() -> str:
    """
    Return a summary list of all candidates in the database.

    Returns:
        JSON string: { "success": bool, "count": int, "data": list[dict] }
    """
    try:
        rows = _db_list_candidates()
        return json.dumps({"success": True, "count": len(rows), "data": rows})
    except Exception as exc:
        logger.exception("list_all_candidates: DB error")
        return json.dumps({"success": False, "count": 0, "data": [], "message": str(exc)})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("ResumeIQ MCP Server starting (stdio transport)…")
    mcp.run(transport="stdio")