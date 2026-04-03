"""
mcp/mcp_server.py
MCP Server – exposes candidate database operations as MCP tools.
The Resume Parser Agent's MCP client calls these tools to persist
extracted resume data into PostgreSQL.

Start with:
    python mcp/mcp_server.py
"""

import json
import logging
import sys
import os

# Allow imports from backend root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp.server.fastmcp import FastMCP
from schema.db_schema import get_connection
from config.settings import MCP_SERVER_HOST, MCP_SERVER_PORT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP("ResumeIQ-DB-Server")


# ─────────────────────────────────────────────────────────────────────────────
# MCP Tools
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def save_candidate(candidate_json: str) -> str:
    """
    Upsert a candidate record into the candidates table.

    Args:
        candidate_json: JSON string with candidate fields extracted from resume.
            Required fields: first_name, last_name, email
            Optional: phone, linkedin_url, skills, skill_experience, education,
                      total_experience_years, current_company, current_job_title,
                      raw_text, source_file

    Returns:
        JSON string: {"success": bool, "candidate_id": int, "message": str}
    """
    try:
        data: dict = json.loads(candidate_json)
    except json.JSONDecodeError as exc:
        return json.dumps({"success": False, "candidate_id": None, "message": f"Invalid JSON: {exc}"})

    required = ["first_name", "last_name", "email"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return json.dumps({"success": False, "candidate_id": None, "message": f"Missing required fields: {missing}"})

    sql = """
        INSERT INTO candidates (
            first_name, last_name, email, phone, linkedin_url,
            skills, skill_experience, education,
            total_experience_years, current_company, current_job_title,
            raw_text, source_file
        ) VALUES (
            %(first_name)s, %(last_name)s, %(email)s, %(phone)s, %(linkedin_url)s,
            %(skills)s::jsonb, %(skill_experience)s::jsonb, %(education)s::jsonb,
            %(total_experience_years)s, %(current_company)s, %(current_job_title)s,
            %(raw_text)s, %(source_file)s
        )
        ON CONFLICT (email) DO UPDATE SET
            first_name              = EXCLUDED.first_name,
            last_name               = EXCLUDED.last_name,
            phone                   = EXCLUDED.phone,
            linkedin_url            = EXCLUDED.linkedin_url,
            skills                  = EXCLUDED.skills,
            skill_experience        = EXCLUDED.skill_experience,
            education               = EXCLUDED.education,
            total_experience_years  = EXCLUDED.total_experience_years,
            current_company         = EXCLUDED.current_company,
            current_job_title       = EXCLUDED.current_job_title,
            raw_text                = EXCLUDED.raw_text,
            source_file             = EXCLUDED.source_file,
            updated_at              = CURRENT_TIMESTAMP
        RETURNING id;
    """

    params = {
        "first_name":               data.get("first_name", ""),
        "last_name":                data.get("last_name", ""),
        "email":                    data.get("email", ""),
        "phone":                    data.get("phone", None),
        "linkedin_url":             data.get("linkedin_url", None),
        "skills":                   json.dumps(data.get("skills", [])),
        "skill_experience":         json.dumps(data.get("skill_experience", {})),
        "education":                json.dumps(data.get("education", [])),
        "total_experience_years":   data.get("total_experience_years", 0),
        "current_company":          data.get("current_company", None),
        "current_job_title":        data.get("current_job_title", None),
        "raw_text":                 data.get("raw_text", None),
        "source_file":              data.get("source_file", None),
    }

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            candidate_id = cur.fetchone()[0]
        conn.commit()
        logger.info("Candidate saved/updated: id=%s email=%s", candidate_id, data["email"])
        return json.dumps({"success": True, "candidate_id": candidate_id, "message": "Candidate saved successfully."})
    except Exception as exc:
        conn.rollback()
        logger.exception("Failed to save candidate")
        return json.dumps({"success": False, "candidate_id": None, "message": str(exc)})
    finally:
        conn.close()


@mcp.tool()
def get_candidate_by_email(email: str) -> str:
    """
    Retrieve a candidate record by email address.

    Args:
        email: The candidate's email address.

    Returns:
        JSON string with candidate data or error message.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM candidates WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                return json.dumps({"success": False, "data": None, "message": "Candidate not found."})
            cols = [desc[0] for desc in cur.description]
            candidate = dict(zip(cols, row))
            # Convert non-serialisable types
            for key in ("created_at", "updated_at"):
                if candidate.get(key):
                    candidate[key] = str(candidate[key])
            return json.dumps({"success": True, "data": candidate, "message": "Found."})
    except Exception as exc:
        logger.exception("Failed to fetch candidate")
        return json.dumps({"success": False, "data": None, "message": str(exc)})
    finally:
        conn.close()


@mcp.tool()
def list_all_candidates() -> str:
    """
    Return a summary list of all candidates stored in the database.

    Returns:
        JSON string with list of candidates (id, name, email, experience, skills).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, first_name, last_name, email,
                       current_job_title, total_experience_years, skills, source_file, created_at
                FROM candidates
                ORDER BY created_at DESC
            """)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            candidates = []
            for row in rows:
                rec = dict(zip(cols, row))
                rec["created_at"] = str(rec["created_at"])
                candidates.append(rec)
        return json.dumps({"success": True, "count": len(candidates), "data": candidates})
    except Exception as exc:
        logger.exception("Failed to list candidates")
        return json.dumps({"success": False, "count": 0, "data": [], "message": str(exc)})
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Starting ResumeIQ MCP Server on %s:%s", MCP_SERVER_HOST, MCP_SERVER_PORT)
    mcp.run(transport="sse", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)