"""
agents/resume_parser/agent.py
------------------------------
Resume Parser Sub-Agent.

This is a Google ADK Agent (not LlmAgent — the simpler Agent class
works fine here since all routing is done by the parent user_agent).

Responsibilities:
  1. Call extract_resume_text tool   → gets raw text from PDF/DOCX
  2. Apply EXTRACTION_INSTRUCTION    → LLM structures the text into JSON
  3. Call save_candidate MCP tool    → persists data to PostgreSQL

Tools:
  • extract_resume_text_tool  — registered at definition time (FunctionTool)
  • MCP tools (save_candidate, etc.) — injected at runtime by runner.py
    because MCPToolset requires an active async context to be open.

This agent is registered as a sub-agent of user_agent in agents/agent.py.
"""

from google.adk.agents import Agent

from instructions.data_extraction import EXTRACTION_INSTRUCTION
from tools.resume_extractor import extract_resume_text_tool


resume_parser_agent = Agent(
    model="gemini-2.5-flash",
    name="resume_parser_agent",
    description=(
        "Parses a resume file to extract structured candidate data "
        "and saves it to the database via MCP tools."
    ),
    instruction=EXTRACTION_INSTRUCTION,
    tools=[
        extract_resume_text_tool,
        # NOTE: MCP tools (save_candidate etc.) are injected at runtime
        # by runner.py → resume_parser_agent.tools += [mcp_tools]
    ],
)