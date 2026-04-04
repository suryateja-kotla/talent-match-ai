import logging
import os
import sys
from contextlib import asynccontextmanager


from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

logger = logging.getLogger(__name__)

_MCP_SERVER_SCRIPT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "mcp_server.py")
)
_PYTHON = sys.executable

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@asynccontextmanager
async def get_mcp_toolset():
    """
    Async context manager — yields a live MCPToolset (stdio transport).
    """
    logger.info("Spawning MCP server: %s %s", _PYTHON, _MCP_SERVER_SCRIPT)

    env = {**os.environ, "RESUMEIQ_BACKEND_ROOT": _BACKEND_ROOT}

    # Setup the standard server parameters
    server_params = StdioServerParameters(
        command=_PYTHON,
        args=[_MCP_SERVER_SCRIPT],
        env=env,
    )

    # Initialize the toolset with the parameters
    toolset = MCPToolset(connection_params=server_params)
    
    try:
        yield toolset
    finally:
        await toolset.close()
        logger.info("MCP server process closed.")