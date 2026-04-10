from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    user_role: str = "user"
    session_id: str = "default_user"
    # Notice: candidate_id is removed; the backend session handles it automatically.

class ChatResponse(BaseModel):
    reply: str
    