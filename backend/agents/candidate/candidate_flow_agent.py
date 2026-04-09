from agents.candidate.application_agent import application_agent
from agents.candidate.job_matching_agent import job_matching_agent
from agents.candidate.resume_parser_agent import resume_parser_agent
from instructions.candidate_flow_instruction import CANDIDATE_FLOW_INSTRUCTION as CF
from google.adk import Agent

candidate_flow_agent = Agent(
    name="candidate_flow_agent",
    description="Strict candidate workflow agent for resume → location → job matching → application",
    instruction=CF,
    sub_agents=[
        resume_parser_agent,
        job_matching_agent,
        application_agent
    ]
)