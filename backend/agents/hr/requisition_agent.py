from google.adk.agents import Agent

from instructions.requisition_instruction import REQUISITION_INSTRUCTION
from mcp_layer.mcp_client import get_mcp_toolset

# ✅ Proper MCP tool injection (supported in your setup)
requisition_agent = Agent(
    model="gemini-2.5-flash",
    name="requisition_agent",
    description=(
        "An HR assistant that extracts skills, location, role, and experience from prompts. "
        "It interactively clarifies missing data, presents a preview for HR approval, "
        "and persists the final requisition to the database via MCP tools only after confirmation."
    ),
    instruction=(
        f"{REQUISITION_INSTRUCTION}\n\n"
        "OPERATIONAL PROTOCOL:\n"
        "1. Extract: Role, Skills, Location, and Experience.\n"
        "2. Validate: If any field is missing, ask the HR user specifically for that info.\n"
        "3. Preview: Once all data is gathered, display a structured summary to the user.\n"
        "4. Confirm: Wait for the user to say 'OK' or 'Proceed' before calling the database storage tool.\n\n"

        "IMPORTANT:\n"
        "- Use ONLY the tool `save_job`\n"
        "- Do NOT use create_job\n"
    ),
    tools=[
        get_mcp_toolset  # 🔥 IMPORTANT: pass function, NOT call it
    ],
)