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
        return json.dumps([])

    try:
        jobs = json.loads(filtered_jobs_json) if isinstance(filtered_jobs_json, str) else filtered_jobs_json
    except Exception:
        return json.dumps([])

    if not jobs:
        return json.dumps([])

    client = genai.Client()
    scored_results = []

    for job in jobs:

        prompt = f"""
You are an expert recruiter.

CANDIDATE:
Skills: {json.dumps(candidate.get('skill_experience', {}))}
Experience: {candidate.get('total_experience_years', 0)}

JOB:
Title: {job.get('title')}
Skills: {json.dumps(job.get('required_skills', []))}
Experience: {job.get('experience_years', 0)}

Return JSON:
{{
 "match_score": number between 0-100
}}
"""

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            raw = response.text.strip()

            if raw.startswith("```"):
                raw = raw.split("```")[1].strip().replace("json", "").strip()

            score_data = json.loads(raw)

            score = score_data.get("match_score", 0)

        except Exception:
            score = 0

        scored_results.append({
            "job_id": job.get("job_id"),
            "title": job.get("title"),  
            "score": score               
        })

    ranked = sorted(scored_results, key=lambda x: x["score"], reverse=True)

    filtered = [j for j in ranked if j["score"] >= 60]   

    return json.dumps(filtered)
    
    


def fetch_candidate(candidate_id: int) -> dict:

    raw = get_candidate_by_id(candidate_id)

    response = json.loads(raw)

    return response.get("data", {})