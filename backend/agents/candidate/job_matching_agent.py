#agents/candidate/job_matching_agent.py

from google.adk.agents import Agent
from tools.job_matching import fetch_candidate, filter_jobs_by_location, score_jobs_with_llm
from instructions.job_matching_instruction import JOB_MATCHING_INSTRUCTION as JM

job_matching_agent = Agent(
    name="job_matching_agent",
    model="gemini-2.5-flash",
    description=(
        "Matches a candidate profile to job postings using DB-backed filtering "
        "and LLM-based scoring."
    ),
   instruction=JM,
    tools=[filter_jobs_by_location, score_jobs_with_llm, fetch_candidate],
)