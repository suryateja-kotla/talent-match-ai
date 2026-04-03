"""
api/resume_routes.py
FastAPI routes for resume upload, parsing, and candidate listing.
"""

import os
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from agents.resume_parser_agent import run_resume_parser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resume", tags=["Resume"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_files", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-and-parse")
async def upload_and_parse_resume(file: UploadFile = File(...)):
    """
    Upload a resume file (PDF or DOCX) and trigger the AI parsing pipeline.
    The extracted candidate data is automatically saved to PostgreSQL.
    """
    allowed_extensions = {".pdf", ".docx", ".doc"}
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {allowed_extensions}",
        )

    # Save uploaded file locally
    dest_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    logger.info("Resume uploaded: %s", dest_path)

    # Run agent
    result = await run_resume_parser(dest_path)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return JSONResponse(content=result)


@router.get("/candidates")
async def list_candidates():
    """List all parsed candidates from the database."""
    from schema.db_schema import get_connection
    import json

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, first_name, last_name, email,
                       current_job_title, total_experience_years,
                       skills, source_file, created_at
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
        return JSONResponse(content={"count": len(candidates), "data": candidates})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()


@router.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: int):
    """Retrieve full candidate details by ID."""
    from schema.db_schema import get_connection

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM candidates WHERE id = %s", (candidate_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Candidate not found.")
            cols = [desc[0] for desc in cur.description]
            rec = dict(zip(cols, row))
            for key in ("created_at", "updated_at"):
                if rec.get(key):
                    rec[key] = str(rec[key])
        return JSONResponse(content=rec)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()