from google.adk.agents import Agent
from mcp_layer.mcp_server import save_job
from instructions.requisition_instruction import REQUISITION_INSTRUCTION

requisition_agent = Agent(
    model="gemini-2.5-flash",
    name="requisition_agent",
    description="Collects job details, generates a professional JD, previews it for HR approval, and saves the requisition only after confirmation.",
    instruction=REQUISITION_INSTRUCTION,  
    tools=[save_job],
)