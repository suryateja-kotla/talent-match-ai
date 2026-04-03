from fastapi import APIRouter
from pydantic import BaseModel
from agents.orchestrator_agent import OrchestratorAgent

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    role: str  # "hr" or "user"

class ChatResponse(BaseModel):
    response: str

orchestrator = OrchestratorAgent()

from fastapi import HTTPException

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print("Incoming request:", request)

        result = await orchestrator.handle(request.message, request.role)

        print("Result:", result)

        return ChatResponse(response=result)

    except Exception as e:
        print("🔥 ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))