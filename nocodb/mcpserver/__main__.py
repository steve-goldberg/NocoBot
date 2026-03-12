"""Entry point for running MCP server as a module.

Usage:
    # stdio mode (for local Claude Desktop)
    python -m nocodb.mcpserver

    # HTTP mode (for deployment)
    python -m nocodb.mcpserver --http
    python -m nocodb.mcpserver --http --port 8001 --host 0.0.0.0

Environment variables:
    NOCODB_URL: NocoDB server URL (required)
    NOCODB_TOKEN: API token or JWT (required)
    NOCODB_BASE_ID: Base ID to work with (required)
    MCP_PORT: HTTP port (default: 8000)
    MCP_HOST: HTTP host (default: 0.0.0.0)
"""

import argparse
import os

from .server import mcp


def main():
    parser = argparse.ArgumentParser(description="NocoDB MCP Server")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run as HTTP server instead of stdio",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="HTTP port (default: 8000, or MCP_PORT env var)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "0.0.0.0"),
        help="HTTP host (default: 0.0.0.0, or MCP_HOST env var)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on file changes (development mode)",
    )

    args = parser.parse_args()

    run_kwargs = {}
    if args.reload:
        run_kwargs["reload"] = True

    if args.http:
        # HTTP transport for deployment (streamable HTTP at /mcp endpoint)
        mcp.run(transport="http", host=args.host, port=args.port, **run_kwargs)
    else:
        # stdio transport for local Claude Desktop
        mcp.run(**run_kwargs)


if __name__ == "__main__":
    main()
