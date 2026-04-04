import asyncio
import os
import sys
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_flow():
    # 1. Point to your MCP server script
    server_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "mcp_server.py"))
    
    # 2. Setup the stdio parameters (passing down environment variables for DB access)
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env={**os.environ}
    )

    print("🚀 Spawning MCP Server over stdio...")
    
    # 3. Connect to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ MCP Session Initialized successfully.\n")

            # --- TEST 1: Save a Candidate ---
            print("📝 [TEST 1] Executing Tool: save_candidate...")
            dummy_candidate = {
                "first_name": "Suryateja",
                "last_name": "Developer",
                "email": "surya.test@sailssoftware.com",
                "skills": ["Python", "Spring Boot", "Agentic AI", "PostgreSQL"],
                "total_experience_years": 1.5,
                "current_company": "Sails Software"
            }
            
            save_result = await session.call_tool("save_candidate", {"candidate_json": dummy_candidate})
            save_data = json.loads(save_result.content[0].text)
            print(f"Server Response: {json.dumps(save_data, indent=2)}\n")

            # --- TEST 2: Get Candidate by Email ---
            print("🔍 [TEST 2] Executing Tool: get_candidate_by_email...")
            email_to_fetch = "surya.test@sailssoftware.com"
            get_result = await session.call_tool("get_candidate_by_email", {"email": email_to_fetch})
            get_data = json.loads(get_result.content[0].text)
            print(f"Server Response: {json.dumps(get_data, indent=2)}\n")

            # --- TEST 3: List All Candidates ---
            print("📋 [TEST 3] Executing Tool: list_all_candidates...")
            list_cand_result = await session.call_tool("list_all_candidates", {})
            list_cand_data = json.loads(list_cand_result.content[0].text)
            print(f"Total Candidates Found: {list_cand_data.get('count')}")
            # Just printing the first one to keep logs clean
            if list_cand_data.get("data"):
                print(f"First Candidate in list: {json.dumps(list_cand_data['data'][0], indent=2)}\n")

            # --- TEST 4: List All Jobs ---
            print("💼 [TEST 4] Executing Tool: list_all_jobs...")
            list_jobs_result = await session.call_tool("list_all_jobs", {})
            list_jobs_data = json.loads(list_jobs_result.content[0].text)
            print(f"Total Active Jobs Found: {list_jobs_data.get('count')}")
            print(f"Server Response: {json.dumps(list_jobs_data, indent=2)}\n")
            
            print("🎉 All tests completed successfully!")

if __name__ == "__main__":
    # Ensure dependencies are installed before running
    # pip install mcp
    asyncio.run(test_mcp_flow())