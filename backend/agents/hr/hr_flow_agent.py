from google.adk.agents import Agent
from agents.hr.requisition_agent import requisition_agent
from instructions.hr_flow_instruction import HR_FLOW_INSTRUCTION as HR

hr_flow_agent = Agent(
    name="hr_flow_agent",
    model="gemini-2.5-flash",
    description="Handles all HR-related queries including job creation and general conversation",
    instruction=HR,
    tools=[],
    sub_agents=[requisition_agent]
)