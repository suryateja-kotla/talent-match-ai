# test_save_job.py
from mcp_layer.mcp_server import save_job

response = save_job({
    "job_title": "Backend Developer",
    "job_type": "full-time",
    "required_skills": ["Python", "FastAPI"],
    "min_experience_years": 2,
    "max_experience_years": 5,
    "job_description": "Build APIs",
    "qualifications": "B.Tech"
})

print(response)