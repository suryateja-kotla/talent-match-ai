"""
agents/agent.py
----------------
Root Orchestrator — user_agent.

This is the top-level ADK Agent that receives every user request.
It does NOT process anything itself — it only routes to the correct sub-agent.

Current sub-agents:
  • resume_parser_agent — triggered when the user provides a resume file_path

Future sub-agents (add to sub_agents list when ready):
  • job_matching_agent  — matches candidates to open jobs
  • application_agent   — auto-applies candidates to matched jobs
  • requisition_agent   — creates job requisitions from HR prompts
"""

from google.adk.agents import Agent

from agents.resume_parser.agent import resume_parser_agent


user_agent = Agent(
    model="gemini-2.5-flash",
    name="user_agent",
    description="Handles user requests and routes them to the appropriate sub-agent.",
    instruction="""
You are the ResumeIQ Orchestrator Agent.
Your only job is to understand the user's request and delegate it to the right sub-agent.
Do NOT process or answer anything yourself.

Routing rules:
  - If the user provides a file_path pointing to a resume (.pdf or .docx),
    delegate the entire request to resume_parser_agent.
  - Pass the file_path exactly as given — do not modify it.
  - Return the exact JSON response that the sub-agent produces.
  - If the request is unclear, ask for clarification.
""",
    sub_agents=[resume_parser_agent],
)