# =============================================================================
# agents/job_matching/tools.py
# =============================================================================

import json
from google import genai

from mcp_layer.mcp_server import get_jobs_by_location
from mcp_layer.mcp_client import call_mcp_tool
# ---------------------------------------------------------------------------
# Tool 1 — DB-based location filter (STRICT match, NO remote)
# ---------------------------------------------------------------------------

def filter_jobs_by_location(location: str) -> str:
    """
    This will be resolved via MCP tool injection at runtime.
    DO NOT import the function manually.
    """
    return call_mcp_tool("get_jobs_by_location", {"location": location})

# ---------------------------------------------------------------------------
# Tool 2 — LLM scoring (optimized)
# ---------------------------------------------------------------------------

def score_jobs_with_llm(candidate_json: str, filtered_jobs_json: str) -> str:
    print("🔥 TOOL 2 CALLED (LLM)")

    candidate = json.loads(candidate_json)

    try:
        jobs = json.loads(filtered_jobs_json)
    except Exception:
        print("❌ Invalid jobs JSON:", filtered_jobs_json)
        return json.dumps([])

    if not jobs:
        return json.dumps([])

    client = genai.Client()

    scored_results = []

    for job in jobs:
        prompt = f"""
You are an expert technical recruiter.

CANDIDATE:
- Title: {candidate.get('current_job_title', 'N/A')}
- Experience: {candidate.get('total_experience_years', 0)} years
- Skills: {json.dumps(candidate.get('skill_experience', {}))}

JOB:
- Title: {job.get('title')}
- Required Skills: {json.dumps(job.get('required_skills', []))}
- Min Experience: {job.get('min_experience_years', 0)}
- Max Experience: {job.get('max_experience_years', 0)}

Score 0–100.

Return JSON:
{{
  "match_score": int
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
            print("❌ LLM ERROR:", e)
            score_data = {"match_score": 0}

        scored_results.append({
            "candidate_id": candidate.get("id"),
            "job_id": job.get("job_id"),
            "match_score": score_data.get("match_score", 0),
        })

    ranked = sorted(scored_results, key=lambda x: x["match_score"], reverse=True)

    return json.dumps(ranked)