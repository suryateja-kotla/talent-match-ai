from google.adk import Agent

candidate_flow_agent = Agent(
    name="candidate_flow_agent",
    description="Handles candidate related tasks like resume, jobs, applications",
    instruction="""
You are the Candidate Flow Agent.

Always respond exactly with:
CANDIDATE FLOW TRIGGERED
"""
)