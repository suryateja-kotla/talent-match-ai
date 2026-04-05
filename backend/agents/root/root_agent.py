from google.adk.agents import Agent # Agent is the preferred alias
from agents.candidate.candidate_flow_agent import candidate_flow_agent
from agents.hr.requisition_agent import requisition_agent
 
APP_NAME = "multi_agent_app"
 
root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="Orchestrator agent that routes user queries to correct sub-agents",
    instruction="""
You are a smart orchestrator agent.
 When you route, ALWAYS say which agent you selected.

Format:
Routing to: <agent_name>
Your job is to understand the user's intent and route to the correct agent.
 
Routing rules:
- If the user is a job seeker / candidate:
  → use candidate_flow_agent
- If the user is HR / recruiter:
  → use requisition_agent
 
Examples:
"improve my resume" → candidate_flow_agent  
"apply for jobs" → candidate_flow_agent  
"i am looking for jobs" → candidate_flow_agent  
 
"create job posting" → requisition_agent  
"i am hr" → requisition_agent  
"hire developer" → requisition_agent  
 
IMPORTANT RULES:
- Always choose ONE correct agent
- Always respond with a final answer
- Never stay silent
- Do not ask unnecessary questions
""",
    sub_agents=[
        candidate_flow_agent,
        requisition_agent
    ]
)