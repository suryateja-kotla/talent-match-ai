import logging
import os
import shutil
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from runner import run_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resume", tags=["Resume"])
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_files", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


@router.post("/upload-and-parse")
async def upload_and_parse(file: UploadFile = File(...), session_id: str = Form(...)):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' is not supported. Please upload one of: {sorted(ALLOWED_EXTENSIONS)}")
    raw_dest_path = os.path.abspath(os.path.join(UPLOAD_DIR, filename))
    safe_dest_path = raw_dest_path.replace("\\", "/")
    try:
        with open(raw_dest_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
    except OSError as exc:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail=f"Could not save file: {exc}")
    prompt = f"""[USER] [SYSTEM COMMAND]
    
The resume has been saved at: '{safe_dest_path}'.
1. Use your tools to parse and save this candidate.
2. Once saved, confirm to the user that their profile is ready.
3. Ask the user which city/location they want to find jobs in."""
    
    logger.info(f"Triggering pipeline for uploaded file: {safe_dest_path}")
    clean_reply = await run_agent(prompt, session_id)
    return JSONResponse(content={
        "success": True,
        "message": "Resume processed.",
        "reply": clean_reply,
        "session_id": session_id
    })