import os
import logging
import json
from google.adk.tools import FunctionTool
from mcp_layer.mcp_server import save_candidate

logger = logging.getLogger(__name__)

def extract_resume_text(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return _fail(f"File not found: {file_path}")
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return _from_pdf(file_path)
    if ext in (".docx", ".doc"):
        return _from_docx(file_path)
    return _fail(f"Unsupported format: {ext}")

def _from_pdf(file_path: str) -> dict:
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        full_text = "\n".join(pages).strip()
        if not full_text:
            return _fail("No extractable text in PDF")
        return {"success": True, "text": full_text, "error": ""}
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return _fail(str(e))


def _from_docx(file_path: str) -> dict:
    try:
        from docx import Document
        doc = Document(file_path)
        lines = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(lines).strip()
        if not text:
            return _fail("Empty DOCX")
        return {"success": True, "text": text, "error": ""}
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return _fail(str(e))

def save_candidate_to_db(candidate_data: dict) -> dict:
    try:
        result_json = save_candidate(candidate_data)
        result = json.loads(result_json)
        if not result.get("success"):
            raise ValueError(result.get("message", "Unknown error from save_candidate"))
        return {"success": True, "candidate_id": result.get("candidate_id"), "error": ""}
    except Exception as e:
        logger.error(f"Failed to save candidate to DB: {e}")
        return _fail(str(e))

def _fail(msg: str) -> dict:
    return {"success": False, "text": "", "error": msg}
    
extract_resume_text_tool = FunctionTool(func=extract_resume_text)
save_candidate_tool = FunctionTool(func=save_candidate_to_db)