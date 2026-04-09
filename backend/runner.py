import json
import re
import logging
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from agents.root.root_agent import root_agent

APP_NAME = "talent-match-ai"
session_service = InMemorySessionService()
logger = logging.getLogger(__name__)

async def get_or_create_session(session_id: str):
    session_id = str(session_id)
    existing = await session_service.get_session(
        user_id=session_id, session_id=session_id, app_name=APP_NAME
    )
    if existing:
        return existing
    return await session_service.create_session(
        user_id=session_id, session_id=session_id, app_name=APP_NAME
    )

def process_reply(reply_text: str, session) -> str:
    id_match = re.search(r'"candidate_id"\s*:\s*(\d+)', reply_text)
    if id_match:
        c_id = int(id_match.group(1))
        session.state["candidate_id"] = c_id
        session.state["resume_uploaded"] = True
        logger.info(f"Syncing Session: candidate_id={c_id}")

    clean_text = re.sub(r'```json.*?```', '', reply_text, flags=re.DOTALL)
    clean_text = re.sub(r'\{[^{}]*"candidate_id"[^{}]*\}', '', clean_text, flags=re.DOTALL)
    clean_text = clean_text.strip()

    if not clean_text and id_match:
        return "I've successfully parsed your resume and saved your profile. Where would you like to look for jobs?"
    
    return clean_text or "I encountered an issue processing that. Could you try again?"

async def run_agent(message: str, session_id: str) -> str:
    session = await get_or_create_session(session_id)

    c_id = session.state.get("candidate_id", "None")
    is_uploaded = session.state.get("resume_uploaded", False)
  
    context_block = f"\n[SESSION_CONTEXT: candidate_id={c_id}, resume_provided={is_uploaded}]"
    enhanced_prompt = f"{message}{context_block}"
    
    user_message = types.Content(
        role="user", 
        parts=[types.Part.from_text(text=enhanced_prompt)]
    )
    runner = Runner(
        app_name=APP_NAME, 
        agent=root_agent, 
        session_service=session_service)
    
    reply = ""
    try:
        async for event in runner.run_async(
            user_id=str(session_id), 
            session_id=str(session_id), 
            new_message=user_message
        ):
            if hasattr(event, "author"):
                print(f"AGENT: {event.author}")

            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        reply += part.text
    except Exception as e:
        logger.error(f"Runner error: {e}")
        return "Sorry, something went wrong. Please try again."

    return process_reply(reply, session)