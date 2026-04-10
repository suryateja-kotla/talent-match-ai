import logging
from fastapi import APIRouter, HTTPException

from schema.chat_model import ChatRequest, ChatResponse
from runner import run_agent
from schema.db_schema import list_applications_by_candidate, list_jobs

logger = logging.getLogger(__name__)

# Create the router for these specific endpoints
router = APIRouter()

@router.post("/api/route/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        logger.info(f"Role: {req.user_role} | Session: {req.session_id}")
        message = req.message.strip()

        if not message:
            return ChatResponse(reply="Please enter a message.")

        role = req.user_role or "hr"
        prompt = f"[{role.upper()}] {message}"

        logger.info(f" Sending to agent: {prompt}")

        # Call run_agent without candidate_id
        reply = await run_agent(prompt, req.session_id)
        
        if not reply:
            reply = " I couldn't generate a response. Please try again."

        logger.info(f" Agent response: {reply}")
        return ChatResponse(reply=reply)

    except Exception as e:
        logger.exception("Error in chat endpoint")
        raise HTTPException(
            status_code=500,
            detail="Internal server error in chat endpoint"
        )

@router.get("/api/jobs")
def get_jobs():
    try:
        jobs = list_jobs()
        return {"jobs": jobs}
    except Exception:
        logger.exception("Failed to fetch jobs")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs")
    
    
    
@router.get("/api/applications/{candidate_id}")
def get_applications(candidate_id: int):
    try:
        apps = list_applications_by_candidate(candidate_id)
        return {"applications": apps}
    except Exception:
        logger.exception("Failed to fetch applications")
        raise HTTPException(status_code=500, detail="Failed to fetch applications")