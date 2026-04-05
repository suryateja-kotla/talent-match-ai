# test_mapping.py

from mcp_layer.mcp_server import map_candidate_to_job

response = map_candidate_to_job(
    candidate_id=1,
    job_id=1
)

print(response)