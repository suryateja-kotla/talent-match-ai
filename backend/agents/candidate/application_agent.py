from google.adk.agents import Agent
from tools.application_agent_tool import apply_to_jobs
from instructions.application_instruction import APPLICATION_INSTRUCTION as AI

application_agent = Agent(
    name="application_agent",
    description=AI,
    tools=[apply_to_jobs],
)