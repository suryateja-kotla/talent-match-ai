import os
import logging
from google.adk.tools import FunctionTool

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


def _fail(msg: str) -> dict:
    return {"success": False, "text": "", "error": msg}


extract_resume_text_tool = FunctionTool(func=extract_resume_text)