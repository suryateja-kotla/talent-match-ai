# agents/hr/hr_flow_agent.py
from google.adk.agents import Agent   # ← was `from google.adk import Agent` which doesn't exist

hr_flow_agent = Agent(
    name="hr_flow_agent",
    model="gemini-2.5-flash",
    description="Routes HR queries to the requisition agent",
    instruction="""
You are the HR Flow Agent.

Classify the user input and route accordingly:
- If the message is about job creation, hiring, posting, or requisition → transfer to requisition_agent
- Otherwise → ask the user to clarify their HR-related request

Always transfer to requisition_agent for job-related requests.
""",
    tools=[],
)