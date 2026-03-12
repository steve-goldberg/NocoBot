"""NocoDB MCP Server.

A FastMCP server exposing NocoDB SDK functionality as MCP tools.

Usage:
    python -m nocodb.mcpserver              # Run with stdio transport
    fastmcp run nocodb/mcp/server.py:mcp    # Via fastmcp CLI
    fastmcp dev nocodb/mcp/server.py:mcp    # Dev mode with inspector
"""

from .server import mcp

__all__ = ["mcp"]
