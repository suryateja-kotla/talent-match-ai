"""
api/resume_routes.py
--------------------
Resume API — FastAPI router.

WHY ONLY ONE ENDPOINT?
  Right now the system's job is to parse resumes and store candidates.
  The only interaction needed from the UI (or curl) is:
    POST /resume/upload-and-parse → send file, get back candidate_id

  Listing / fetching candidates can be done directly via PostgreSQL
  during development. A GET /resume/candidates endpoint will be added
  here once the Angular UI integration begins.

Endpoint:
  POST /resume/upload-and-parse
    • Validates file type (.pdf / .docx only)
    • Saves the file to sample_files/uploads/
    • Calls runner.run_resume_parsing(file_path)
    • Returns the candidate_id and success status
"""

import logging
import os
import shutil

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from runner import run_resume_parsing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["Resume"])

# Uploaded files land here; directory is created automatically if missing
UPLOAD_DIR = os.path.join(
    os.path.dirname(__file__), "..", "sample_files", "uploads"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


@router.post("/upload-and-parse")
async def upload_and_parse(file: UploadFile = File(...),session_id: str = Form(...)):
    """
    Upload a resume file and run the AI parsing pipeline.

    The pipeline:
      file upload → save to disk → ADK agent →
      extract text → LLM parse → MCP save_candidate → PostgreSQL

    Returns:
        200: { "success": true, "candidate_id": 1, "message": "...", "raw_response": "..." }
        400: unsupported file type
        500: agent or DB error
    """
    # ── validate extension ────────────────────────────────────────────────────
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"File type '{ext}' is not supported. "
                f"Please upload one of: {sorted(ALLOWED_EXTENSIONS)}"
            ),
        )

    # ── save to uploads directory ─────────────────────────────────────────────
    dest_path = os.path.join(UPLOAD_DIR, filename)
    try:
        with open(dest_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
    except OSError as exc:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail=f"Could not save file: {exc}")

    logger.info("Resume saved to %s — starting pipeline", dest_path)

    # ── run agent pipeline ────────────────────────────────────────────────────
    result = await run_resume_parsing(dest_path, session_id)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return JSONResponse(content=result)