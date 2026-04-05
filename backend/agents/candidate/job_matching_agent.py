# =============================================================================
# agents/job_matching/agent.py
# =============================================================================

from google.adk.agents import Agent
from tools.job_matching import fetch_candidate, filter_jobs_by_location, score_jobs_with_llm

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
  "candidate_id": int,
  "location": "string"
}

Follow EXACTLY:

STEP 0 — Call fetch_candidate with "candidate_id"

STEP 1 — Call filter_jobs_by_location with "location"

STEP 2 — Call score_jobs_with_llm with:
  - candidate_id
  - filtered_jobs_json

STEP 3 — Return ONLY the JSON from Step 2
""",
    tools=[filter_jobs_by_location, score_jobs_with_llm, fetch_candidate],
)