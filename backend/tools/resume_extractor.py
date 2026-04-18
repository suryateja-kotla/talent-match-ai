"""
tools/resume_extractor.py
--------------------------
`extract_resume_text` — ADK FunctionTool

Called by resume_parser_agent as Step 1 of every parsing run.
Reads a resume file from disk and returns the raw text content.

Supported formats:
  .pdf   — extracted with pdfplumber (handles multi-page, columns, tables)
  .docx  — extracted with python-docx
"""

import logging
import os

from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Public function (also registered as ADK tool below)
# ─────────────────────────────────────────────────────────────────────────────

def extract_resume_text(file_path: str) -> dict:
    """
    Extract raw text from a resume file (.pdf or .docx).

    Args:
        file_path: Path to the resume file on disk.

    Returns:
        {
          "success": bool,
          "text":    str,   # full extracted text (empty string on failure)
          "error":   str    # error description (empty string on success)
        }
    """
    # ── existence check ───────────────────────────────────────────────────────
    if not os.path.exists(file_path):
        return _fail(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    # ── dispatch by extension ─────────────────────────────────────────────────
    if ext == ".pdf":
        return _from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return _from_docx(file_path)
    else:
        return _fail(f"Unsupported format '{ext}'. Please use .pdf or .docx")


# ─────────────────────────────────────────────────────────────────────────────
# Format handlers
# ─────────────────────────────────────────────────────────────────────────────

def _from_pdf(file_path: str) -> dict:
    try:
        import pdfplumber
    except ImportError:
        return _fail("pdfplumber is not installed. Run: pip install pdfplumber")

    try:
        pages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)

        full_text = "\n".join(pages).strip()

        if not full_text:
            return _fail("PDF has no extractable text. It may be scanned/image-based.")

        logger.info("PDF extracted: %d chars | file=%s", len(full_text), file_path)
        return {"success": True, "text": full_text, "error": ""}

    except Exception as exc:
        logger.exception("PDF extraction error")
        return _fail(str(exc))


def _from_docx(file_path: str) -> dict:
    try:
        from docx import Document
    except ImportError:
        return _fail("python-docx is not installed. Run: pip install python-docx")

    try:
        doc   = Document(file_path)
        lines = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(lines).strip()

        if not full_text:
            return _fail("DOCX file appears to be empty.")

        logger.info("DOCX extracted: %d chars | file=%s", len(full_text), file_path)
        return {"success": True, "text": full_text, "error": ""}

    except Exception as exc:
        logger.exception("DOCX extraction error")
        return _fail(str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _fail(reason: str) -> dict:
    logger.error("extract_resume_text failed: %s", reason)
    return {"success": False, "text": "", "error": reason}


# ─────────────────────────────────────────────────────────────────────────────
# ADK FunctionTool wrapper — this is what the agent uses
# ─────────────────────────────────────────────────────────────────────────────

extract_resume_text_tool = FunctionTool(func=extract_resume_text)