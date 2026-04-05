from google.adk import Agent

hr_flow_agent = Agent(
    name="hr_flow_agent",
    description="Routes HR queries to requisition agent",
    instruction="""
    You are the HR Flow Agent.

    Classify the user input.

    If it is about job creation, hiring, or requisition:
    → Respond EXACTLY: REQUISITION

    Otherwise:
    → Respond EXACTLY: NONE
    """
)