"""
agents/resume_parser_agent.py
Google ADK agent that:
 1. Reads a resume file (PDF/DOCX) via the extract_resume_text tool.
 2. Parses structured data from the raw text using an LLM.
 3. Saves the parsed data to PostgreSQL via MCP tools (save_candidate).
"""

import json
import logging
import os
from typing import AsyncGenerator

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
from google import genai

from config.settings import GOOGLE_API_KEY, MCP_SERVER_URL
from instructions.data_extraction import EXTRACTION_INSTRUCTION
from tools.resume_extractor import extract_resume_text_tool

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# ADK / Gemini initialisation
# ─────────────────────────────────────────────────────────────────────────────
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
client = genai.Client()

MODEL = "gemini-2.0-flash"


# ─────────────────────────────────────────────────────────────────────────────
# Agent factory
# ─────────────────────────────────────────────────────────────────────────────

def create_resume_parser_agent(mcp_toolset: MCPToolset) -> LlmAgent:
    """Build and return the Resume Parser LLM Agent."""
    return LlmAgent(
        model=MODEL,
        name="resume_parser_agent",
        description=(
            "Parses resume files to extract structured candidate data "
            "and stores it in the database via MCP."
        ),
        instruction=EXTRACTION_INSTRUCTION,
        tools=[
            extract_resume_text_tool,  # reads file -> raw text
            mcp_toolset,               # save_candidate, get_candidate_by_email, list_all_candidates
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# High-level runner
# ─────────────────────────────────────────────────────────────────────────────

async def run_resume_parser(file_path: str) -> dict:
    """
    Parse a resume file and persist the extracted candidate to the DB.

    Args:
        file_path: Path to the resume file (.pdf or .docx).

    Returns:
        dict with keys: success (bool), candidate_id (int|None), message (str),
                        extracted_data (dict|None)
    """
    mcp_toolset = MCPToolset(
        connection_params=SseServerParams(url=f"{MCP_SERVER_URL}/sse")
    )

    try:
        agent = create_resume_parser_agent(mcp_toolset)
        session_service = InMemorySessionService()
        runner = Runner(
            agent=agent,
            app_name="resumeiq",
            session_service=session_service,
        )

        session = await session_service.create_session(
            app_name="resumeiq",
            user_id="system",
        )

        prompt = (
            f"Parse the resume at file_path='{file_path}'.\n"
            "Step 1: Call extract_resume_text with that file_path to get raw text.\n"
            "Step 2: Extract structured data following your instructions.\n"
            "Step 3: Call save_candidate with a JSON string of the extracted data "
            "        (include the source_file field set to the file_path).\n"
            "Step 4: Return the final JSON result from save_candidate."
        )

        from google.adk.types import Content, Part

        result_text = ""
        async for event in runner.run_async(
            user_id="system",
            session_id=session.id,
            new_message=Content(role="user", parts=[Part(text=prompt)]),
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        result_text += part.text

        logger.info("Agent final response: %s", result_text)

        # Try to parse the save_candidate response from the final text
        try:
            # The agent may embed JSON in its reply
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "success": result.get("success", False),
                    "candidate_id": result.get("candidate_id"),
                    "message": result.get("message", ""),
                    "raw_response": result_text,
                }
        except Exception:
            pass

        return {
            "success": True,
            "candidate_id": None,
            "message": "Agent completed. Check DB for candidate record.",
            "raw_response": result_text,
        }

    except Exception as exc:
        logger.exception("Resume parser agent failed")
        return {"success": False, "candidate_id": None, "message": str(exc), "raw_response": ""}
    finally:
        await mcp_toolset.close()