import asyncio

from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types as genai_types

from agents.root.root_agent import root_agent, APP_NAME

load_dotenv()  # Load environment variables from .env file
session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def run_chat(message: str):
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id="user_001",
    )

    user_message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=message)],
    )

    async for event in runner.run_async(
        user_id="user_001",
        session_id=session.id,
        new_message=user_message,
    ):
        print("EVENT:", event)  # 🔥 debug

        if event.is_final_response():
            if event.content and event.content.parts:
                print("\n✅ FINAL RESPONSE:")
                print(event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(run_chat("Improve my resume"))