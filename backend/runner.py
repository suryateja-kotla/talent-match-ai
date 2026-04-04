import json
import logging
import re

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv

# --- Import your Multi-Agent Hierarchy ---
from agents.root.root_agent import root_agent, APP_NAME
from agents.candidate.resume_parser_agent import resume_parser_agent
from mcp_integration.mcp_client import get_mcp_toolset 

load_dotenv()

Content = types.Content
Part = types.Part
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Public entry point — called by api/resume_routes.py
# ─────────────────────────────────────────────────────────────────────────────

async def run_resume_parsing(file_path: str) -> dict:
    """
    Orchestrates the Multi-Agent flow for resume parsing.
    
    Flow: 
    1. Start MCP Server (DB Connection)
    2. Inject DB tools into the Specialist (Resume Parser)
    3. Send File Path to the Root Agent (Orchestrator)
    4. Root Agent delegates to Resume Parser
    5. Cleanup and return structured JSON
    """
    logger.info("Multi-agent pipeline starting for file: %s", file_path)

    # 1. Open the MCP Stdio connection (spawns mcp_server.py)
    async with get_mcp_toolset() as mcp_tools:

        # 2. Inject DB tools into the Sub-Agent
        # We do this here because the sub-agent is the one actually calling 'save_candidate'
        original_tools = list(resume_parser_agent.tools)
        resume_parser_agent.tools = original_tools + [mcp_tools]

        try:
            # 3. Initialize Session & Runner pointed at the ROOT
            session_service = InMemorySessionService()
            runner = Runner(
                agent=root_agent,  # <--- Root decides who does the work
                app_name=APP_NAME,
                session_service=session_service,
            )

            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id="system_user",
            )

            # 4. Prepare the message for the Root Agent
            # We provide the file path as context so the specialist can find it
            instruction = f"Parse the resume located at: {file_path}"
            
            message = Content(
                role="user",
                parts=[Part(text=instruction)],
            )

            # 5. Stream events and capture final response
            final_text = ""
            async for event in runner.run_async(
                user_id="system_user",
                session_id=session.id,
                new_message=message,
            ):
                # Log events for debugging (Multi-agent delegation events show up here)
                if event.is_final_response() and event.content and getattr(event.content, "parts", None):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_text += part.text

            logger.info("Multi-agent task completed.")
            return _parse_final_response(final_text)

        finally:
            # 6. CRITICAL: Always restore original tools to keep the agent 'pure'
            resume_parser_agent.tools = original_tools


# ─────────────────────────────────────────────────────────────────────────────
# Response Parser (Kept from your original logic)
# ─────────────────────────────────────────────────────────────────────────────

def _parse_final_response(text: str) -> dict:
    """Extracts JSON from the agent's prose response."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return {
                "success": data.get("success", True),
                "candidate_id": data.get("candidate_id"),
                "message": data.get("message", "Processed successfully."),
                "raw_response": text,
            }
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "candidate_id": None,
        "message": "Task complete. Please check the DB manually.",
        "raw_response": text,
    }
