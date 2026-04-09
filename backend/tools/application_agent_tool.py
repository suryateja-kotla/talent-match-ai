import logging
from schema import db_schema

logger = logging.getLogger(__name__)


def apply_to_jobs(candidate_id: int, job_matches: list[dict]) -> dict:
    """
    Apply candidate to real jobs from job matching agent.

    Args:
        candidate_id: ID of the candidate
        job_matches: list of dicts from job matching agent
                     e.g. [{"job_id": 1, "score": 0.85}, ...]
                     score can be 0-1 float OR 0-100 int — both handled
    """
    try:
        results = []

        for match in job_matches:
            job_id = int(match["job_id"])

            # Convert score to decimal (0.00 - 1.00)
            raw_score = match.get("score", 0)
            if raw_score > 1:
                score = round(raw_score / 100, 4)   # e.g. 85 → 0.85
            else:
                score = round(float(raw_score), 4)  # e.g. 0.85 → 0.85

            logger.info(f"Applying: candidate={candidate_id}, job={job_id}, score={score}")

            # Save to DB — no schema change, uses existing create_application
            db_schema.create_application(candidate_id, job_id, score)

            results.append({
                "job_id": job_id,
                "match_score": score,
                "status": "applied"
            })

        return {
            "success": True,
            "candidate_id": candidate_id,
            "total_applied": len(results),
            "applications": results
        }

    except Exception as e:
        logger.error(f"Application error: {e}")
        return {
            "success": False,
            "message": str(e)
        }