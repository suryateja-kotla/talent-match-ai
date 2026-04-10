from google.adk.agents import Agent
from instructions.resume_parser_prompt import EXTRACTION_INSTRUCTION
from tools.resume_extractor import extract_resume_text_tool, save_candidate_tool

resume_parser_agent = Agent(
    model="gemini-2.5-flash",
    name="resume_parser_agent",
    description=(
        "Parses a resume file to extract structured candidate data "
        "and saves it to the database."
    ),
    instruction=EXTRACTION_INSTRUCTION,
    tools=[
        extract_resume_text_tool, 
        save_candidate_tool
    ],
)