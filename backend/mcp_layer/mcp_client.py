import asyncio
import os
import sys
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import asynccontextmanager
import logging

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

logger = logging.getLogger(__name__)
@asynccontextmanager
async def get_mcp_toolset():
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
    async with stdio_client(server_params) as session:
        print("✅ MCP Client connected to server.")
        toolset = MCPToolset(session)
        try:
            yield toolset
        finally:
            await toolset.close()
            logger.info("MCP server process closed.")

if __name__ == "__main__":
    # Ensure dependencies are installed before running
    # pip install mcp
    asyncio.run(get_mcp_toolset())