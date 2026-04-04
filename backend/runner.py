import asyncio

import traceback

import os

import json

import re

import logging

from dotenv import load_dotenv
 
# ─────────────────────────────────────────────────────────────

# ✅ Load environment variables

# ─────────────────────────────────────────────────────────────

load_dotenv()
 
print("🔑 GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))
 
# ─────────────────────────────────────────────────────────────

# ✅ Imports (ADK + Agents)

# ─────────────────────────────────────────────────────────────

from google.adk.sessions import InMemorySessionService

from google.adk.runners import Runner

from google.genai import types as genai_types
 
from agents.root.root_agent import root_agent, APP_NAME

from agents.candidate.resume_parser_agent import resume_parser_agent

from mcp_layer.mcp_client import get_mcp_toolset
 
logger = logging.getLogger(__name__)
 
# ─────────────────────────────────────────────────────────────

# ✅ Shared Session + Runner (USED BY ALL FLOWS)

# ─────────────────────────────────────────────────────────────

session_service = InMemorySessionService()
 
runner = Runner(

    agent=root_agent,

    app_name=APP_NAME,

    session_service=session_service,

)
 
# ─────────────────────────────────────────────────────────────

# 🤖 1. CHAT FLOW (Frontend → Root Agent)

# ─────────────────────────────────────────────────────────────

async def run_agent(message: str, session_id: str) -> str:

    """

    Generic chat entry point.

    Used by: FastAPI chat endpoint

    """

    print("🚀 ENTERED run_agent")
 
    try:

        session = await session_service.create_session(

            app_name=APP_NAME,

            user_id=session_id,

        )
 
        user_message = genai_types.Content(

            role="user",

            parts=[genai_types.Part(text=message)],

        )
 
        print("📤 Sending to root_agent...")
 
        reply_text = ""
 
        async for event in runner.run_async(

            user_id=session_id,

            session_id=session.id,

            new_message=user_message,

        ):

            print("📩 EVENT:", event)
 
            if event.is_final_response():

                if event.content and event.content.parts:

                    reply_text = event.content.parts[0].text
 
        print("🎯 FINAL RESPONSE:", reply_text)
 
        return reply_text or "⚠️ Empty response"
 
    except Exception as e:

        print("❌ ERROR in run_agent:", str(e))

        traceback.print_exc()

        return f"❌ ERROR: {str(e)}"
 
 
# ─────────────────────────────────────────────────────────────

# 📄 2. RESUME PARSING FLOW (MCP + DB + Specialist Agent)

# ─────────────────────────────────────────────────────────────

async def run_resume_parsing(file_path: str) -> dict:

    """

    Multi-agent resume parsing pipeline.
 
    Flow:

    MCP → root_agent → resume_parser_agent → DB

    """

    logger.info("📄 Resume parsing started: %s", file_path)
 
    # 1. Start MCP (DB tools)

    async with get_mcp_toolset() as mcp_tools:
 
        # 2. Inject tools into specialist agent

        original_tools = list(resume_parser_agent.tools)

        resume_parser_agent.tools = original_tools + [mcp_tools]
 
        try:

            # 3. Create session

            session = await session_service.create_session(

                app_name=APP_NAME,

                user_id="system_user",

            )
 
            # 4. Send instruction to root agent

            instruction = f"Parse the resume located at: {file_path}"
 
            message = genai_types.Content(

                role="user",

                parts=[genai_types.Part(text=instruction)],

            )
 
            final_text = ""
 
            # 5. Run multi-agent flow

            async for event in runner.run_async(

                user_id="system_user",

                session_id=session.id,

                new_message=message,

            ):

                if event.is_final_response():

                    if event.content and event.content.parts:

                        final_text += event.content.parts[0].text
 
            logger.info("✅ Resume parsing completed")
 
            return _parse_final_response(final_text)
 
        finally:

            # 6. Restore original tools (VERY IMPORTANT)

            resume_parser_agent.tools = original_tools
 
 
# ─────────────────────────────────────────────────────────────

# 🧠 3. RESPONSE PARSER (JSON extraction)

# ─────────────────────────────────────────────────────────────

def _parse_final_response(text: str) -> dict:

    """

    Extract JSON from agent response.

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

            pass
 
    return {

        "success": True,

        "candidate_id": None,

        "message": "Task complete. Check DB manually.",

        "raw_response": text,

    }
 
 
# ─────────────────────────────────────────────────────────────

# 🔧 OPTIONAL: Local testing

# ─────────────────────────────────────────────────────────────

async def run_chat(message: str):

    response = await run_agent(message, "test_user")

    print("\n✅ FINAL:", response)
 
 
if __name__ == "__main__":

    asyncio.run(run_chat("post a job"))
 