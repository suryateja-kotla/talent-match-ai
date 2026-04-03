"""
mcp/mcp_client.py
MCP Client helper used by agents to call tools on the MCP Server.
Wraps google.adk.tools.mcp_tool.MCPToolset for SSE transport.
"""

import logging
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from config.settings import MCP_SERVER_URL

logger = logging.getLogger(__name__)


def get_mcp_toolset() -> MCPToolset:
    """
    Return an MCPToolset connected to the ResumeIQ MCP Server via SSE.
    Each call creates a fresh connection; close it when done.
    """
    logger.info("Connecting to MCP Server at %s/sse", MCP_SERVER_URL)
    return MCPToolset(
        connection_params=StdioServerParameters(
            command="python",
            args=["mcp/mcp_server.py"]
        )
    )