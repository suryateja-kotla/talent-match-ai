from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat import router as chat_router
import os
from dotenv import load_dotenv
load_dotenv()
print(f"DEBUG: Using Project -> {os.getenv('GOOGLE_CLOUD_PROJECT')}")
print(f"DEBUG: Use Vertex? -> {os.getenv('GOOGLE_GENAI_USE_VERTEXAI')}")
app = FastAPI()

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)