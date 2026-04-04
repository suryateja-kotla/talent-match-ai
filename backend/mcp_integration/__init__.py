# Only export the client helper.
# mcp_server.py is spawned as a subprocess — never imported directly.
from .mcp_client import get_mcp_toolset

__all__ = ["get_mcp_toolset"]