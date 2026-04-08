from google.adk.agents import Agent

from instructions.requisition_instruction import REQUISITION_INSTRUCTION


requisition_agent = Agent(
    model="gemini-2.5-flash",
    name="requisition_agent",
    description=(
        "An HR assistant that collects job details, auto-generates or enhances the job description, "
        "presents a full preview for HR approval, and saves the requisition only after confirmation."
    ),
    instruction=(
        f"{REQUISITION_INSTRUCTION}\n\n"
        "OPERATIONAL PROTOCOL:\n"
        "1. Extract: job_title, location, experience_required, skills_required, number_of_positions.\n"
        "2. Validate: Ask for any missing required fields.\n"
        "3. Generate JD: Auto-generate a professional JD. If HR gave a partial one, enhance it.\n"
        "4. Preview: Show the full summary including generated JD. Invite HR to review or request changes.\n"
        "5. Revise: If HR requests JD changes, apply them and show updated preview again.\n"
        "6. Confirm: Call save_job only when HR says OK / Proceed / Yes / Sure.\n"
        "7. Respond: Confirm success with Job ID or report failure.\n\n"
        "Greetings or small talk must be forwarded to hr_flow_agent. "
        "This agent handles requisition creation only."
    ),
    tools=[],
)