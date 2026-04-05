# =============================================================================
# agents/job_matching/agent.py
# =============================================================================

from google.adk.agents import Agent
from tools.job_matching import filter_jobs_by_location, score_jobs_with_llm

APP_NAME = "job_matching_agent"
MODEL_ID = "gemini-2.5-flash"

job_matching_agent = Agent(
    name=APP_NAME,
    model=MODEL_ID,
    description=(
        "Matches a candidate profile to job postings using DB-backed filtering "
        "and LLM-based scoring."
    ),
    instruction="""
You are a Job Matching Agent.

Input JSON:
{
  "candidate": {...},
  "location": "string"
}

Follow EXACTLY:

STEP 1 — Call filter_jobs_by_location with "location"

STEP 2 — Call score_jobs_with_llm with:
  - candidate_json
  - filtered_jobs_json

STEP 3 — Return ONLY the JSON from Step 2
""",
    tools=[filter_jobs_by_location, score_jobs_with_llm],
)