"""Shared views tools for NocoDB MCP server.

Provides operations for public/shared view links:
- shared_views_list: List all shared views for a table
- shared_view_create: Create a public link for a view
- shared_view_update: Update shared view settings
- shared_view_delete: Remove a public link (requires confirm=True)
"""

from typing import Optional

from ..server import mcp
from ..dependencies import get_client
from ..errors import wrap_api_error
from ..models import SharedViewsListResult, SharedViewResult, SharedViewDeleteResult


@mcp.tool
@wrap_api_error
def shared_views_list(table_id: str) -> SharedViewsListResult:
    """List all shared (public) views for a table.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")

    Returns:
        SharedViewsListResult with list of shared views.
    """
    client = get_client()

    result = client.shared_views_list(table_id)
    shared_views = result.get("list", [])

    return SharedViewsListResult(shared_views=shared_views)


@mcp.tool
@wrap_api_error
def shared_view_create(
    view_id: str,
    password: Optional[str] = None,
) -> SharedViewResult:
    """Create a public link for a view.

    This makes the view accessible via a unique URL without authentication.

    Args:
        view_id: The view ID (e.g., "vw_xxx")
        password: Optional password to protect the shared view

    Returns:
        SharedViewResult with the UUID for the public URL.

    Note: The full public URL will be: {nocodb_url}/shared/{uuid}
    """
    client = get_client()

    result = client.shared_view_create(view_id, password=password)

    return SharedViewResult(
        uuid=result.get("uuid", ""),
        url=result.get("url"),
    )


@mcp.tool
@wrap_api_error
def shared_view_update(
    view_id: str,
    password: Optional[str] = None,
) -> SharedViewResult:
    """Update a shared view's settings.

    Args:
        view_id: The view ID (e.g., "vw_xxx")
        password: New password (or None to remove password protection)

    Returns:
        SharedViewResult with updated settings.
    """
    client = get_client()

    result = client.shared_view_update(view_id, password=password)

    return SharedViewResult(
        uuid=result.get("uuid", ""),
        url=result.get("url"),
    )


@mcp.tool(annotations={
    "title": "Delete Shared View",
    "destructiveHint": True,
    "idempotentHint": True,
})
@wrap_api_error
def shared_view_delete(
    view_id: str,
    confirm: bool = False,
) -> SharedViewDeleteResult:
    """Remove public access from a view.

    The public link will no longer work. The view itself is not deleted.

    Args:
        view_id: The view ID (e.g., "vw_xxx")
        confirm: Must be True to proceed with removal

    Returns:
        SharedViewDeleteResult with success status.
    """
    if not confirm:
        from fastmcp.exceptions import ToolError
        raise ToolError(
            "Set confirm=True to remove public access. "
            "The shared link will stop working."
        )

    client = get_client()

    client.shared_view_delete(view_id)

    return SharedViewDeleteResult(
        success=True,
        message=f"Public link removed for view {view_id}",
    )
