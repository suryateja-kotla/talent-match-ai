"""
agents/requisition_agent/agent.py
--------------------------------

Requisition Agent (Job Creator).

Responsibilities:
  1. Accept HR query (job requirements, role details, etc.)
  2. Use LLM with REQUISITION_INSTRUCTION to structure job data
  3. Call MCP tool (create_job) to save job into database

Tools:
  • MCP tools (create_job, etc.) — injected at runtime by runner.py
"""

from google.adk.agents import Agent

from instructions.requisition_instruction import REQUISITION_INSTRUCTION


requisition_agent = Agent(
    model="gemini-2.5-flash",
    name="requisition_agent",
    description=(
        "Creates structured job requisitions from HR input "
        "and saves them to the database via MCP tools."
    ),
    instruction=REQUISITION_INSTRUCTION,
    tools=[
        # MCP tools (create_job etc.) will be injected at runtime
        # Example:
        # requisition_agent.tools += [mcp_tools]
    ],
)