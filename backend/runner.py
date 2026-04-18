"""
runner.py
---------
ResumeIQ Session Runner.

This is the ONLY place where:
  • MCPToolset is opened (spawns mcp_server.py via stdio)
  • MCP tools are injected into resume_parser_agent
  • ADK Runner + InMemorySessionService are created
  • The agent run is executed and the final response collected

Keeping all of this here means agents/agent.py and
agents/resume_parser/agent.py stay pure — no runtime side-effects.

Called by: api/resume_routes.py → run_resume_parsing(file_path)
"""

import json
import logging
import re

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.agent import user_agent
from agents.resume_parser.agent import resume_parser_agent
from mcp_integration.mcp_client import get_mcp_toolset
from dotenv import load_dotenv
load_dotenv()
Content = types.Content
Part = types.Part
logger = logging.getLogger(__name__)

APP_NAME = "resumeiq"


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point — called by the FastAPI route
# ─────────────────────────────────────────────────────────────────────────────

async def run_resume_parsing(file_path: str) -> dict:
    """
    Execute the full resume parsing pipeline for one resume file.

    Steps:
      1. Open MCPToolset  → spawns mcp_server.py as child process (stdio)
      2. Inject MCP tools → resume_parser_agent.tools gets save_candidate etc.
      3. Create ADK session + Runner pointed at user_agent
      4. Send user message: "Parse the resume at file_path='...'"
      5. user_agent delegates to resume_parser_agent
      6. resume_parser_agent: extract_resume_text → LLM parse → save_candidate
      7. Collect final agent response and return structured dict

    Args:
        file_path: Absolute path to a .pdf or .docx resume file.

    Returns:
        {
            "success":      bool,
            "candidate_id": int | None,
            "message":      str,
            "raw_response": str   ← full final text from the agent
        }
    """
    logger.info("Pipeline starting for: %s", file_path)

    async with get_mcp_toolset() as mcp_tools:

        # ── Inject MCP tools into resume_parser_agent ─────────────────────
        # The agent is defined without MCP tools because MCPToolset needs
        # an active async context. We extend the tools list here and restore
        # it afterwards so the agent definition stays clean.
        original_tools = list(resume_parser_agent.tools)
        resume_parser_agent.tools = original_tools + [mcp_tools]

        try:
            # ── ADK session + runner ──────────────────────────────────────
            session_service = InMemorySessionService()
            runner = Runner(
                agent=user_agent,
                app_name=APP_NAME,
                session_service=session_service,
            )

            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id="system",
            )

            # ── User message → orchestrator ───────────────────────────────
            message = Content(
                role="user",
                parts=[Part(text=f"Parse the resume at file_path='{file_path}'")],
            )

            # ── Stream agent events, capture final response ───────────────
            final_text = ""
            async for event in runner.run_async(
                user_id="system",
                session_id=session.id,
                new_message=message,
            ):
                if event.is_final_response() and event.content and getattr(event.content, "parts", None):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_text += part.text

            logger.info("Pipeline completed for: %s", file_path)
            logger.debug("Agent final text: %s", final_text)

            return _parse_final_response(final_text)

        finally:
            # Always restore original tools list
            resume_parser_agent.tools = original_tools


# ─────────────────────────────────────────────────────────────────────────────
# Response parser
# ─────────────────────────────────────────────────────────────────────────────

def _parse_final_response(text: str) -> dict:
    """
    Extract a structured result dict from the agent's final text.

    The agent is instructed to return the raw JSON from save_candidate.
    We parse it here. If no JSON is found (agent returned prose), we
    still return success=True since the DB write may have succeeded.
    """
    # Try to find a JSON object anywhere in the response
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return {
                "success":      data.get("success", True),
                "candidate_id": data.get("candidate_id"),
                "message":      data.get("message", "Done."),
                "raw_response": text,
            }
        except json.JSONDecodeError:
            pass

    # Fallback — agent finished but returned plain text
    return {
        "success":      True,
        "candidate_id": None,
        "message":      "Agent completed. Check the candidates table to verify.",
        "raw_response": text,
    }