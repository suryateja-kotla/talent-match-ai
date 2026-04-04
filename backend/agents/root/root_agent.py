from google.adk import Agent
from agents.candidate.candidate_flow_agent import candidate_flow_agent
from agents.hr.requisition_agent import requisition_agent

APP_NAME = "multi_agent_app"

root_agent = Agent(
    name="root_agent",
    description="Orchestrator agent that routes user queries",
    instruction="""
You are a smart orchestrator.

Decide which agent to use:

- If the user is a job seeker / candidate:
  → use candidate_flow_agent

- If the user is HR / recruiter:
  → use requisition_agent

Examples:

"improve my resume" → candidate_flow_agent  
"apply for jobs" → candidate_flow_agent  
"create job posting" → requisition_agent  

Always choose the correct tool.
""",
    sub_agents=[
        candidate_flow_agent,
        requisition_agent
    ]
)