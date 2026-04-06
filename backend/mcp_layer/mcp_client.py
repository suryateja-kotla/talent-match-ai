import os
import sys
import logging
from contextlib import asynccontextmanager

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_mcp_toolset():
    server_script = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "mcp_server.py")
    )

    logger.info(f"🚀 Spawning MCP Server: {server_script}")

    # ✅ MCPToolset takes StdioServerParameters directly
    # It manages the subprocess + stdio_client internally
    # Do NOT manually call stdio_client() and pass the session in
    toolset = MCPToolset(
        connection_params=StdioServerParameters(
            command=sys.executable,
            args=[server_script],
            env={**os.environ},
        )
    )

    print("🚀 Spawning MCP Server over stdio...")
    try:
        yield toolset
    finally:
        if hasattr(toolset, "close"):
            await toolset.close()
        logger.info("MCP server process closed.")

if __name__ == "__main__":
    # Ensure dependencies are installed before running
    # pip install mcp
    asyncio.run(get_mcp_toolset())