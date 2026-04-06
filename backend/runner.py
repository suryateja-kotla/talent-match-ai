import asyncio
import json
import logging
import os
import re
from dotenv import load_dotenv
import config.settings

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types as genai_types

from agents.root.root_agent import root_agent, APP_NAME
from agents.hr.requisition_agent import requisition_agent
from agents.candidate.resume_parser_agent import resume_parser_agent
from mcp_layer.mcp_client import get_mcp_toolset

logger = logging.getLogger(__name__)
load_dotenv()

logger.info(f"GCP Project: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'NOT SET')}")
logger.info(f"GCP Location: {os.environ.get('GOOGLE_CLOUD_LOCATION', 'NOT SET')}")

APP_NAME = "talent-match-ai"

session_service = InMemorySessionService()
_session_registry: dict[str, str] = {}

# ✅ Single shared runner — defined once
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def _get_or_create_session(session_id: str):
    if session_id in _session_registry:
        adk_id = _session_registry[session_id]
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=session_id,
            session_id=adk_id,
        )
        if session:
            logger.info(f"♻️  Reusing session {adk_id} for {session_id}")
            return session
        logger.warning(f"⚠️  Session {adk_id} gone, recreating...")

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
    )
    _session_registry[session_id] = session.id
    logger.info(f"🆕 Created session {session.id} for {session_id}")
    return session


async def run_agent(message: str, session_id: str) -> str:
    logger.info(f"🚀 run_agent | session={session_id} | msg={message[:80]}")
    original_tools = list(requisition_agent.tools)
    try:
        # ✅ async with — get_mcp_toolset is @asynccontextmanager
        async with get_mcp_toolset() as mcp_tools:
            requisition_agent.tools = [mcp_tools]
            session = await _get_or_create_session(session_id)

            user_message = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=message)],
            )

            reply_text = ""
            async for event in runner.run_async(
                user_id=session_id,
                session_id=session.id,
                new_message=user_message,
            ):
                if event.is_final_response():
                    if event.content and getattr(event.content, "parts", None):
                        reply_text = event.content.parts[0].text

            logger.info(f"🎯 Reply: {reply_text[:100]}")
            return reply_text or "⚠️ Empty response from agent."

    except Exception as e:
        logger.exception("❌ ERROR in run_agent pipeline.")
        return f"❌ ERROR: {str(e)}"
    finally:
        requisition_agent.tools = original_tools


async def run_resume_parsing(file_path: str) -> dict:
    logger.info("📄 Resume parsing: %s", file_path)
    original_tools = list(resume_parser_agent.tools)
    try:
        async with get_mcp_toolset() as mcp_tools:
            resume_parser_agent.tools = original_tools + [mcp_tools]
            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id="system_user",
            )
            message = genai_types.Content(
                role="user",
                parts=[genai_types.Part(
                    text=f"Parse the resume located at: {file_path}"
                )],
            )
            final_text = ""
            async for event in runner.run_async(  # ✅ runner not runner_instance
                user_id="system_user",
                session_id=session.id,
                new_message=message,
            ):
                if event.is_final_response():
                    if event.content and getattr(event.content, "parts", None):
                        final_text += event.content.parts[0].text

            return _parse_final_response(final_text)

    except Exception as e:
        logger.exception("❌ ERROR in run_resume_parsing.")
        return {"success": False, "message": str(e), "raw_response": ""}
    finally:
        resume_parser_agent.tools = original_tools


def _parse_final_response(text: str) -> dict:
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
            logger.warning("Malformed JSON in agent response.")
    return {
        "success": True,
        "candidate_id": None,
        "message": "Task complete, no structured ID returned.",
        "raw_response": text,
    }


async def _run_chat(message: str):
    response = await run_agent(message, "test_user")
    print(f"\n✅ FINAL: {response}")

if __name__ == "__main__":
    asyncio.run(_run_chat("post a job"))