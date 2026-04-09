from google.adk.agents import Agent
from tools.application_agent_tool import apply_to_jobs

application_agent = Agent(
    name="application_agent",
    description="""
    Applies a candidate to matched jobs and saves to database.
    
    - candidate_id: ALWAYS take from session state (already provided in context)
    - job_matches: list of dicts from job_matching_agent
      e.g. [{"job_id": 1, "score": 85}, {"job_id": 2, "score": 72}]
    
    NEVER ask the user for candidate_id. It is always in session state.
    NEVER  show job_id to the user. Use job titles in conversational responses instead.
    """,
    tools=[apply_to_jobs],
)