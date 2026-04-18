"""
sample_files/test_run.py
-------------------------
Direct test runner — bypasses FastAPI, runs the full pipeline end-to-end.

Usage (from backend/ directory):
    python sample_files/test_run.py

Or with a custom resume path:
    python sample_files/test_run.py "C:/Users/you/resumes/john_doe.pdf"
    python sample_files/test_run.py "/home/user/resumes/jane.docx"

What this does:
  1. Initialises PostgreSQL (creates DB + tables if missing)
  2. Runs the ADK agent pipeline on the resume file
     → ADK spawns mcp_server.py as a subprocess (stdio)
     → Agent extracts text, LLM parses it, save_candidate stores it
  3. Queries PostgreSQL and prints what was stored
"""

import asyncio
import json
import logging
import os
import sys

# ── backend root on path ──────────────────────────────────────────────────────
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BACKEND_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("test_run")


# ── Resolve file path ─────────────────────────────────────────────────────────
if len(sys.argv) > 1:
    # Path passed as command-line argument
    RESUME_PATH = os.path.abspath(sys.argv[1])
else:
    # Default: sample resume in the same folder as this script
    RESUME_PATH = os.path.join(os.path.dirname(__file__), "sample_resume.pdf")


# ─────────────────────────────────────────────────────────────────────────────
async def main():
    # ── Step 1: DB init ───────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("ResumeIQ Test Run")
    logger.info("=" * 60)
    logger.info("Resume file : %s", RESUME_PATH)

    if not os.path.exists(RESUME_PATH):
        logger.error("File not found: %s", RESUME_PATH)
        logger.error("Usage: python sample_files/test_run.py <path_to_resume.pdf>")
        sys.exit(1)

    logger.info("")
    logger.info("Step 1 — Initialising database...")
    from schema.db_schema import create_database_if_not_exists, init_db
    create_database_if_not_exists()
    init_db()
    logger.info("Database ready.")

    # ── Step 2: Run pipeline ──────────────────────────────────────────────────
    logger.info("")
    logger.info("Step 2 — Running agent pipeline...")
    logger.info("  (ADK spawns MCP server subprocess, Gemini parses resume)")

    from runner import run_resume_parsing
    result = await run_resume_parsing(RESUME_PATH)

    logger.info("")
    logger.info("─── Agent Result ────────────────────────────────────────")
    logger.info("  success      : %s", result["success"])
    logger.info("  candidate_id : %s", result["candidate_id"])
    logger.info("  message      : %s", result["message"])

    if not result["success"]:
        logger.error("Pipeline failed. Check logs above for details.")
        sys.exit(1)

    # ── Step 3: Verify in DB ──────────────────────────────────────────────────
    logger.info("")
    logger.info("Step 3 — Verifying data in PostgreSQL...")

    from schema.db_schema import get_connection

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if result["candidate_id"]:
                # Fetch the specific candidate we just saved
                cur.execute(
                    "SELECT * FROM candidates WHERE id = %s",
                    (result["candidate_id"],)
                )
                row = cur.fetchone()
                cols = [d[0] for d in cur.description]
                candidate = dict(zip(cols, row)) if row else None
            else:
                # Fallback: fetch the most recently inserted candidate
                cur.execute("""
                    SELECT * FROM candidates
                    ORDER BY created_at DESC LIMIT 1
                """)
                row = cur.fetchone()
                cols = [d[0] for d in cur.description]
                candidate = dict(zip(cols, row)) if row else None
    finally:
        conn.close()

    if not candidate:
        logger.warning("No candidate found in DB. Something may have gone wrong.")
        return

    # ── Print what was stored ─────────────────────────────────────────────────
    logger.info("")
    logger.info("─── Stored in PostgreSQL ────────────────────────────────")
    logger.info("  id                     : %s", candidate.get("id"))
    logger.info("  name                   : %s %s",
                candidate.get("first_name"), candidate.get("last_name"))
    logger.info("  email                  : %s", candidate.get("email"))
    logger.info("  phone                  : %s", candidate.get("phone"))
    logger.info("  linkedin_url           : %s", candidate.get("linkedin_url"))
    logger.info("  current_company        : %s", candidate.get("current_company"))
    logger.info("  current_job_title      : %s", candidate.get("current_job_title"))
    logger.info("  total_experience_years : %s", candidate.get("total_experience_years"))
    logger.info("  source_file            : %s", candidate.get("source_file"))

    # Skills (JSONB)
    skills = candidate.get("skills")
    if skills:
        if isinstance(skills, str):
            skills = json.loads(skills)
        logger.info("  skills (%d)            : %s", len(skills), ", ".join(skills[:10]))
        if len(skills) > 10:
            logger.info("                           ... and %d more", len(skills) - 10)

    # Skill experience (JSONB)
    skill_exp = candidate.get("skill_experience")
    if skill_exp:
        if isinstance(skill_exp, str):
            skill_exp = json.loads(skill_exp)
        logger.info("  skill_experience       :")
        for skill, years in list(skill_exp.items())[:10]:
            logger.info("    %-30s %.1f yrs", skill, years)
        if len(skill_exp) > 10:
            logger.info("    ... and %d more skills", len(skill_exp) - 10)

    # Education (JSONB)
    education = candidate.get("education")
    if education:
        if isinstance(education, str):
            education = json.loads(education)
        logger.info("  education              :")
        for edu in education:
            logger.info("    %s — %s (%s)",
                        edu.get("degree"), edu.get("institution"), edu.get("year"))

    logger.info("")
    logger.info("=" * 60)
    logger.info("Test completed successfully!")
    logger.info("Candidate id=%s is now in the candidates table.",
                candidate.get("id"))
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())