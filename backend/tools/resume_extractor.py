"""
tools/resume_extractor.py
Tool used by the Resume Parser Agent to extract raw text from a resume file.
Supports PDF and DOCX formats.
"""

import os
import logging
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)


def extract_resume_text(file_path: str) -> dict:
    """
    Extract raw text content from a resume file (.pdf or .docx).

    Args:
        file_path: Absolute or relative path to the resume file.

    Returns:
        dict with keys:
            - success (bool)
            - text (str): extracted text, empty string on failure
            - error (str): error message if failed
    """
    if not os.path.exists(file_path):
        return {"success": False, "text": "", "error": f"File not found: {file_path}"}

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".pdf":
            return _extract_pdf(file_path)
        elif ext in (".docx", ".doc"):
            return _extract_docx(file_path)
        else:
            return {
                "success": False,
                "text": "",
                "error": f"Unsupported file type: {ext}. Use .pdf or .docx",
            }
    except Exception as exc:
        logger.exception("Unexpected error extracting '%s'", file_path)
        return {"success": False, "text": "", "error": str(exc)}


def _extract_pdf(file_path: str) -> dict:
    try:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        full_text = "\n".join(text_parts).strip()
        if not full_text:
            return {"success": False, "text": "", "error": "PDF appears to have no extractable text."}
        return {"success": True, "text": full_text, "error": ""}
    except ImportError:
        return {"success": False, "text": "", "error": "pdfplumber not installed. Run: pip install pdfplumber"}


def _extract_docx(file_path: str) -> dict:
    try:
        from docx import Document

        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs).strip()
        if not full_text:
            return {"success": False, "text": "", "error": "DOCX appears to be empty."}
        return {"success": True, "text": full_text, "error": ""}
    except ImportError:
        return {"success": False, "text": "", "error": "python-docx not installed. Run: pip install python-docx"}


# Wrap as a Google ADK FunctionTool
extract_resume_text_tool = FunctionTool(func=extract_resume_text)