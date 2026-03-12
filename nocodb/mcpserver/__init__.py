"""NocoDB MCP Server.

A FastMCP server exposing NocoDB SDK functionality as MCP tools.

Usage:
    python -m nocodb.mcpserver              # Run with stdio transport
    fastmcp run nocodb.mcpserver.server:mcp  # Via fastmcp CLI
    fastmcp dev nocodb.mcpserver.server:mcp  # Dev mode with inspector
"""

from .server import mcp

__all__ = ["mcp"]
