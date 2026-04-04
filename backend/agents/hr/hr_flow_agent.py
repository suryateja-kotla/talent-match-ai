from google.adk import Agent
from agents.hr.requisition_agent import requisition_handler


class HRFlowHandler:
    def handle(self, user_input: str):
        print("🔥 HR FLOW CALLED")
        return requisition_handler.handle(user_input)


# ✅ THIS LINE IS MANDATORY
hr_handler = HRFlowHandler()


# ADK wrapper
hr_flow_agent = Agent(
    name="hr_flow_agent",
    description="Handles HR workflows",
    instruction="""
You are the HR Flow Agent.

Always respond exactly with:
HR FLOW TRIGGERED
"""
)