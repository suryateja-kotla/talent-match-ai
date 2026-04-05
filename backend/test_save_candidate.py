# test_save_candidate.py

from mcp_layer.mcp_server import save_candidate

candidate = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@test.com",
    "phone": "9876543210",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "current_company": "ABC Corp",
    "current_job_title": "Backend Developer",
    "total_experience_years": 3,
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "skill_experience": {
        "Python": 3,
        "FastAPI": 2
    },
    "education": [
        {
            "degree": "B.Tech",
            "institution": "XYZ University",
            "year": "2020"
        }
    ],
    "raw_text": "Sample resume text",
    "source_file": "resume.pdf"
}

response = save_candidate(candidate)
print(response)