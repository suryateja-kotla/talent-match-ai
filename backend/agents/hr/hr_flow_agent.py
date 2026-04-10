# hr_flow_agent.py

from google.adk.agents import Agent
from agents.hr.requisition_agent import requisition_agent
from mcp_layer.mcp_server import list_all_jobs  
from instructions.hr_flow_instruction import HR_FLOW_INSTRUCTION as HRF
hr_flow_agent = Agent(
    name="hr_flow_agent",
    model="gemini-2.5-flash",
    description="Handles all HR queries — general conversation, job creation, and job listing.",
    instruction=HRF,
    tools=[list_all_jobs],           
    sub_agents=[requisition_agent]
)