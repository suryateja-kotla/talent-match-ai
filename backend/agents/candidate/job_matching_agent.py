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

STEP 3 — Count the results returned from Step 2.
Format a conversational response using the ACTUAL job titles and ACTUAL scores.

Example format:
"I found X jobs that match your profile in <location>:

1. <actual job title> — Match Score: <actual score>%
2. <actual job title> — Match Score: <actual score>%

Would you like me to apply to these jobs for you?"

Where X is the actual count of matched jobs.

RULES:
- NEVER return raw JSON to the user
- NEVER show candidate_id or job_id to the user
- Show ACTUAL job title and ACTUAL match score from results
- Always end with "Would you like me to apply to these jobs for you?"
- If no jobs found say: "I could not find any matching jobs in that location. Would you like to try a different location?"
""",
    tools=[filter_jobs_by_location, score_jobs_with_llm, fetch_candidate],
)