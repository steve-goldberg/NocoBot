"""Bases tools for NocoDB MCP server.

Provides introspection operations for bases:
- bases_list: List all bases (to discover available databases)
- base_info: Get details about the configured base

Note: Base creation is not available via API in self-hosted NocoDB.
Use the NocoDB web UI to create new bases.
"""

from ..server import mcp
from ..dependencies import get_client, get_base_id
from ..errors import wrap_api_error
from ..models import BasesListResult, BaseInfoResult


@mcp.tool
@wrap_api_error
def bases_list() -> BasesListResult:
    """List all bases available to the current user.

    Use this to discover base IDs for configuration.

    Returns:
        BasesListResult with list of bases including id and title.

    Note: The MCP server requires NOCODB_BASE_ID to be set.
    This tool helps you find available base IDs if you need
    to configure a different base.
    """
    client = get_client()

    result = client.bases_list()
    bases = result.get("list", [])

    return BasesListResult(bases=bases)


@mcp.tool
@wrap_api_error
def base_info() -> BaseInfoResult:
    """Get detailed information about the currently configured base.

    Returns the base metadata including title and list of tables.

    Returns:
        BaseInfoResult with base id, title, tables, and metadata.
    """
    client = get_client()
    base_id = get_base_id()

    result = client.base_read(base_id)

    return BaseInfoResult(
        id=result.get("id", base_id),
        title=result.get("title", ""),
        tables=result.get("tables", []),
        meta=result.get("meta"),
    )
