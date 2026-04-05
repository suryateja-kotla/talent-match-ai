import logging
import sys
import traceback
import os
import uvicorn
 
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
 
# ✅ Load ENV first
load_dotenv()
 
# ✅ Fix import paths (important for agents & modules)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
 
# ✅ Internal imports
from runner import run_agent
from config.settings import APP_HOST, APP_PORT, LOG_LEVEL
from schema.db_schema import create_database_if_not_exists, init_db
from api.resume_routes import router as resume_router
 
# ─────────────────────────────────────────────────────────────
# 🔧 Logging Setup
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
 
# ─────────────────────────────────────────────────────────────
# 🚀 FastAPI App
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="TalentMatch + ResumeIQ API",
    description="Multi-Agent AI Recruitment System",
    version="2.0.0",
)
 
# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# ─────────────────────────────────────────────────────────────
# 📦 Routers (Resume / other modules)
# ─────────────────────────────────────────────────────────────
app.include_router(resume_router)
 
# ─────────────────────────────────────────────────────────────
# 🧠 Chat Models
# ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    user_role: str = "hr"
    session_id: str = "default_user"
 
 
class ChatResponse(BaseModel):
    reply: str
 
 
# ─────────────────────────────────────────────────────────────
# 🤖 Chat Endpoint (YOUR AGENT)
# ─────────────────────────────────────────────────────────────
@app.post("/api/route/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        logger.info(f"📥 Role Received: {req.user_role}")
        logger.info(f"📥 Request : {req.dict()}")
        message = req.message.strip()
 
        if not message:
            return ChatResponse(reply="⚠️ Please enter a message.")
 
        # ✅ Quick greeting shortcut
        if message.lower() in ["hi", "hello", "hey"]:
            return ChatResponse(
                reply="👋 Hi! I'm your hiring assistant. Describe the role you want to post."
            )
 
        role = req.user_role or "hr"
        prompt = f"[{role.upper()}] {message}"
 
        logger.info(f"🚀 Sending to agent: {prompt}")
 
        reply = await run_agent(prompt, req.session_id)
 
        if not reply:
            reply = "⚠️ I couldn't generate a response. Please try again."
 
        logger.info(f"✅ Agent response: {reply}")
 
        return ChatResponse(reply=reply)
 
    except Exception as e:
        logger.exception("❌ Error in chat endpoint")
        raise HTTPException(
            status_code=500,
            detail="Internal server error in chat endpoint"
        )
 
 
# ─────────────────────────────────────────────────────────────
# ❤️ Health Check
# ─────────────────────────────────────────────────────────────
@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "TalentMatch + ResumeIQ API"
    }
 
 
# ─────────────────────────────────────────────────────────────
# ⚙️ Startup (DB + infra)
# ─────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    logger.info("🚀 Backend starting...")
 
    try:
        create_database_if_not_exists()
        init_db()
        logger.info("✅ Database ready.")
    except Exception:
        logger.exception("❌ Startup failed")
        sys.exit(1)
 
 
# ─────────────────────────────────────────────────────────────
# ▶️ Run
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower(),   # ✅ FIXED typo here
    )