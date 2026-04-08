from email.mime import message
import logging
import sys
import os
import uvicorn

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

# ENV first — before any ADK/google imports
load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# runner is the single source of truth — no Runner created here
from runner import run_agent
from config.settings import APP_HOST, APP_PORT, LOG_LEVEL
from schema.db_schema import create_database_if_not_exists, init_db
from api.resume_routes import router as resume_router
from schema.db_schema import list_jobs

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TalentMatch + ResumeIQ API",
    description="Multi-Agent AI Recruitment System",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router)


# ── Models ────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    user_role: str = "user"
    session_id: str = "default_user"
    candidate_id: int | None = None 
 
 
class ChatResponse(BaseModel):
    reply: str


# ── Chat ──────────────────────────────────────────────────────

@app.post("/api/route/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        logger.info(f"Role: {req.user_role} | Session: {req.session_id}")
        message = req.message.strip()

        if not message:
            return ChatResponse(reply="Please enter a message.")
 
        role = req.user_role or "hr"
        prompt = f"[{role.upper()}] {message}"
 
        logger.info(f" Sending to agent: {prompt}")
        # 🔒 Prevent USER doing HR action
 
        reply = await run_agent(prompt, req.session_id, candidate_id=req.candidate_id)
        if not reply:
            reply = " I couldn't generate a response. Please try again."
 
        #return {"reply": reply}
 
       
        logger.info(f" Agent response: {reply}")
        return ChatResponse(reply=reply)
 
    except Exception as e:
        logger.exception("Error in chat endpoint")
        raise HTTPException(
            status_code=500,
            detail="Internal server error in chat endpoint"
        )
        
    
@app.get("/api/jobs")
def get_jobs():
    try:
        jobs = list_jobs()
        return {"jobs": jobs}
    except Exception:
        logger.exception("Failed to fetch jobs")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs")
 
# ─────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────
@app.get("/")
def health_check():
    return {"status": "ok", "service": "TalentMatch + ResumeIQ API"}


# ── Startup ───────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    logger.info("Backend starting...")
    try:
        create_database_if_not_exists()
        init_db()
        logger.info(" Database ready.")
    except Exception:
        logger.exception("Startup failed")
        sys.exit(1)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower(),
    )
