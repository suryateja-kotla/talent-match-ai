import asyncio
import json
import logging
import os
import re
from dotenv import load_dotenv
import config.settings

# IMPORTANT: Import settings early to ensure Vertex AI environment
# variables (GOOGLE_CLOUD_PROJECT, etc.) are injected into os.environ
# BEFORE the google.genai SDK initializes within the ADK.

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types as genai_types

from agents.root.root_agent import root_agent, APP_NAME
from agents.candidate.resume_parser_agent import resume_parser_agent
from mcp_layer.mcp_client import get_mcp_toolset

logger = logging.getLogger(__name__)

load_dotenv()
# Confirm Vertex AI migration in logs
logger.info("🚀 Initializing ADK Runner routing through Vertex AI.")
logger.info(f"GCP Project: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'NOT SET')}")
logger.info(f"GCP Location: {os.environ.get('GOOGLE_CLOUD_LOCATION', 'NOT SET')}")
# ─────────────────────────────────────────────────────────────
# Shared Session + Runner (Used by all flows)
# ─────────────────────────────────────────────────────────────
session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


_session_registry: dict[str, str] = {}


async def _get_or_create_session(session_id: str):
    if session_id in _session_registry:
        adk_id = _session_registry[session_id]
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=session_id,
            session_id=adk_id,
        )
        if session:
            return session

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
    )
    _session_registry[session_id] = session.id
    return session


#  1. CHAT FLOW (Frontend → Root Agent)


async def run_agent(message: str, session_id: str, candidate_id: int | None) -> str:
    """
    Generic chat entry point. Routes general user queries through the
    root orchestrator agent to the appropriate sub-agent.
    """
    #logger.info(f"🚀 Entering run_agent for session: {session_id}")
    
    try:
        session = await _get_or_create_session(session_id)
        if candidate_id:
            session.state["candidate_id"] = candidate_id
        enhanced_message = f"""
[USER] {message}
SESSION STATE:
resume_uploaded: {session.state.get("resume_uploaded")}
candidate_id: {session.state.get("candidate_id")}

CRITICAL:
Use candidate_id={session.state.get("candidate_id")} for ALL job matching.
DO NOT ask user for it.
"""

        user_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=enhanced_message)],
        )

        logger.debug("📤 Dispatching message to root_agent...")
        reply_text = ""

        async for event in runner.run_async(
            user_id=session_id,
            session_id=session.id,
            new_message=user_message,
        ):
            # 🔍 Try to extract useful info
            if hasattr(event, "author"):
                print(f"AGENT: {event.author}")

            # ✅ Capture final response
            if event.content and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        reply_text += part.text
        return reply_text

    except Exception as e:
        logger.exception("ERROR in run_agent pipeline.")
        return f"ERROR: {str(e)}"


#  2. RESUME PARSING FLOW (MCP + DB + Specialist Agent)


async def run_resume_parsing(file_path: str, session_id: str) -> dict:
    """
    Executes the multi-agent resume parsing pipeline.
    Flow: MCP Tools Injected → Root Agent → Resume Parser Agent → Database Upsert
    """
    logger.info("📄 Resume parsing started for: %s", file_path)

    # 1. Start the MCP server process to access DB tools
    async with get_mcp_toolset() as mcp_tools:

        # 2. Dynamically inject MCP tools into the specialist agent
        original_tools = list(resume_parser_agent.tools)
        resume_parser_agent.tools = original_tools + [mcp_tools]

        try:
            # 3. Create an isolated system session
            session = await _get_or_create_session(session_id)

            # 4. Formulate the direct instruction
            instruction = f"[user] Parse the resume located at: {file_path}"
            message = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=instruction)],
            )

            final_text = ""

            # 5. Execute the runner
            async for event in runner.run_async(
                user_id=session_id,
                session_id=session.id,
                new_message=message,
            ):
                if event.content and getattr(event.content, "parts", None):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_text += part.text

            result = _parse_final_response(final_text)

            session = await _get_or_create_session(session_id)
            session.state["resume_uploaded"] = True
            session.state["candidate_id"] = result.get("candidate_id")

            return result

        finally:
            # 6. Restore original tools to keep the agent definition pure
            resume_parser_agent.tools = original_tools


#  3. RESPONSE PARSER (JSON Extraction)


def _parse_final_response(text: str) -> dict:
    """
    Extracts the structured JSON payload returned by the MCP save_candidate tool
    from the agent's final text response.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)

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
            logger.warning("Agent returned malformed JSON block.")

    # Fallback if no valid JSON block is found
    return {
        "success": True,
        "candidate_id": None,
        "message": "Task complete, but no structured ID returned. Check DB manually.",
        "raw_response": text,
    }


# OPTIONAL: Local Testing Module


async def run_chat(message: str):
    response = await run_agent(message, "test_user")
    print(f"\n FINAL: {response}")


if __name__ == "__main__":
    # Test the orchestrator routing
    asyncio.run(run_chat("post a job"))
