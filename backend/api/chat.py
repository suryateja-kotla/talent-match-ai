# backend/api/chat.py
from unittest import result

from fastapi import APIRouter
from pydantic import BaseModel
from runner import run_agent
 
router = APIRouter()
 
class ChatRequest(BaseModel):
    message: str
    user_role: str  # "hr" or "candidate"
    session_id: str
 
class ChatResponse(BaseModel):
    reply: str
 
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Prepend role context so root_agent routes correctly
    prompt = f"[{req.user_role.upper()}] {req.message}"
    result = await run_agent(prompt, req.session_id)

    return ChatResponse(
        reply=result.get("reply"),
        agent=result.get("agent")
)