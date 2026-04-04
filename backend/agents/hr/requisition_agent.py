from google.adk import Agent

requisition_agent = Agent(
    name="requisition_agent",
    description="Handles HR job creation and requisitions",
    instruction="""
You are the HR Requisition Agent.

Always respond exactly with:
HR FLOW TRIGGERED
"""
)