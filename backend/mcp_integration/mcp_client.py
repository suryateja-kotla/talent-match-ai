"""
mcp/mcp_client.py
-----------------
ResumeIQ MCP Client — stdio transport.

HOW IT WORKS:
  StdioServerParameters tells the ADK MCPToolset to:
    1. Spawn `mcp/mcp_server.py` as a child process using the current Python interpreter.
    2. Communicate with it over stdin / stdout (MCP wire protocol).
    3. Expose the server's registered tools (save_candidate, get_candidate_by_email,
       list_all_candidates) as callable ADK tools inside the agent.

  The caller uses this as an async context manager so the child process is
  always cleaned up properly after the agent run finishes.

Usage (in runner.py):
    async with get_mcp_toolset() as mcp_tools:
        agent.tools += [mcp_tools]
        # ... run agent ...
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.stdio import StdioConnectionParams, StdioServerParams

logger = logging.getLogger(__name__)

# Absolute path to the server script so it works from any working directory
_MCP_SERVER_SCRIPT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "mcp_server.py")
)
_PYTHON = sys.executable  # same interpreter that runs the main app


@asynccontextmanager
async def get_mcp_toolset():
    """
    Async context manager — yields a connected MCPToolset (stdio).

    Spawns mcp_server.py as a child process on entry,
    closes + kills it cleanly on exit.

    Example:
        async with get_mcp_toolset() as mcp_tools:
            # inject mcp_tools into agent, then run the agent
    """
    logger.info("Spawning MCP server: %s %s", _PYTHON, _MCP_SERVER_SCRIPT)

    toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParams(
            command=_PYTHON,
            args=[_MCP_SERVER_SCRIPT],
        )
    )
)
    try:
        yield toolset
    finally:
        await toolset.close()
        logger.info("MCP server process closed.")