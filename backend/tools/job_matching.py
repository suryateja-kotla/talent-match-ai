# =============================================================================
# agents/job_matching/tools.py
# =============================================================================

import json
from google import genai

from mcp_layer.mcp_server import get_jobs_by_location
from mcp_layer.mcp_server import get_candidate_by_id
#from mcp_layer.mcp_client import call_mcp_tool
# ---------------------------------------------------------------------------
# Tool 1 — DB-based location filter (STRICT match, NO remote)
# ---------------------------------------------------------------------------

def filter_jobs_by_location(location: str) -> list:
    """
    This will be resolved via MCP tool injection at runtime.
    DO NOT import the function manually.
    """
    
    raw = get_jobs_by_location(location)

    parsed = json.loads(raw)

    return parsed

# ---------------------------------------------------------------------------
# Tool 2 — LLM scoring (optimized)
# ---------------------------------------------------------------------------

def score_jobs_with_llm(candidate_id: int, filtered_jobs_json: str) -> str:

    candidate = fetch_candidate(candidate_id)
    if not candidate:
        print(" Candidate not found — aborting scoring")
        return json.dumps([])

    try:
        if isinstance(filtered_jobs_json, str):
            jobs = json.loads(filtered_jobs_json)
        else:
            jobs = filtered_jobs_json
    except Exception:
        print(" Invalid jobs JSON:", filtered_jobs_json)
        return json.dumps([])

    if not jobs:
        return json.dumps([])

    client = genai.Client()

    scored_results = []
    for job in jobs:
        if isinstance(job, str):
            try:
                job = json.loads(job)
            except Exception:
                print("Invalid job item:", job)
                continue

        if not isinstance(job, dict):
            print("Skipping non-dict job:", job)
            continue
        prompt = f"""
You are an expert technical recruiter.

CANDIDATE:
- Title: {candidate.get('current_job_title', 'N/A')}
- Experience: {candidate.get('total_experience_years', 0)} years
- Skills: {json.dumps(candidate.get('skill_experience', {}))}

JOB:
- Title: {job.get('title')}
- Required Skills: {json.dumps(job.get('required_skills', []))}
- Experience Required: {job.get('experience_years', 0)} years

Score 0–100.

Return JSON:
{{
  "candidate_id": {candidate.get("id")},
  "job_id": {job.get("job_id")},
  "match_score": <score>
}}
"""

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            raw = response.text.strip()

            # Clean markdown if needed
            if raw.startswith("```"):
                raw = raw.split("```")[1].strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()

            score_data = json.loads(raw)

        except Exception as e:
            print("LLM ERROR:", e)
            score_data = {"match_score": 0}

        scored_results.append({
            "candidate_id": candidate.get("id"),
            "job_id": job.get("job_id"),
            "match_score": score_data.get("match_score", 0),
        })

    ranked = sorted(scored_results, key=lambda x: x["match_score"], reverse=True)
    filtered_ranked = [job for job in ranked if job["match_score"] >= 70]
    #return json.dumps(filtered_ranked)
    return filtered_ranked
    
    


def fetch_candidate(candidate_id: int) -> dict:

    raw = get_candidate_by_id(candidate_id)

    response = json.loads(raw)

    return response.get("data", {})