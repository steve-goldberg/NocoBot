"""NocoDB MCP Server.

A FastMCP server exposing NocoDB SDK functionality as MCP tools.

Usage:
    python -m nocodb.mcpserver                   # Run with stdio transport
    fastmcp run -m nocodb.mcpserver              # Via fastmcp CLI
    fastmcp dev inspector -m nocodb.mcpserver    # Dev mode with inspector

Both fastmcp invocations need module mode (-m). The CLI resolves a bare
server spec as a filesystem path, and server.py cannot be loaded as a
standalone file because it imports its siblings relatively -- it only works
as part of the package. `fastmcp dev` is a command group as of FastMCP 4, so
the inspector is reached through `dev inspector` rather than `dev` directly.
"""

from .server import mcp

__all__ = ["mcp"]
