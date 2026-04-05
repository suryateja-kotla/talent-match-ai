
from google.adk import Agent

application_agent = Agent(
    name="application_Agent",
    description="Handles candidate workflow: resume → location → job matching → auto application",

    instruction=
    """
    you are application agent
    """

)