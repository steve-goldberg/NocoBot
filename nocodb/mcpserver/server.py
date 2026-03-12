"""NocoDB MCP Server.

FastMCP server exposing NocoDB SDK functionality as MCP tools.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from .dependencies import init_dependencies, cleanup_dependencies


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[None]:
    """Server lifespan handler for initializing dependencies.

    Initializes the NocoDB client and configuration on startup,
    and cleans up on shutdown.
    """
    # Startup: Initialize NocoDB client from environment
    config, client = init_dependencies()
    print(f"NocoDB MCP server connected to {config.url} (base: {config.base_id})")

    yield

    # Shutdown: Cleanup
    cleanup_dependencies()
    print("NocoDB MCP server shutdown")


# Create the FastMCP server
mcp = FastMCP(
    "NocoDB",
    lifespan=lifespan,
)


# =============================================================================
# Health check endpoint for monitoring
# =============================================================================
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for load balancers and monitoring."""
    return JSONResponse({"status": "ok"})


# =============================================================================
# Import tool modules to register them with the server
# =============================================================================
# Tools are registered when their modules are imported.
# Each module uses @mcp.tool decorator to register tools.

from .tools import (  # noqa: E402, F401
    records,
    bases,
    tables,
    fields,
    links,
    views,
    view_filters,
    view_sorts,
    view_columns,
    shared_views,
    webhooks,
    members,
    attachments,
    storage,
    export,
    schema,
)

# Import resources module to register resources with the server
from . import resources  # noqa: E402, F401
