from google.adk.agents import Agent
from agents.candidate.candidate_flow_agent import candidate_flow_agent
from agents.hr.hr_flow_agent import hr_flow_agent
from instructions.root_instruction import ROOT_INSTRUCTION

root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    description="Root orchestrator that enforces strict separation between HR and Candidate workflows and holds global MCP tools.",
    instruction=ROOT_INSTRUCTION,
    sub_agents=[
        candidate_flow_agent,
        hr_flow_agent
    ],
    tools=[] 
)