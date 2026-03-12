"""View sorts tools for NocoDB MCP server.

Provides CRUD operations for view sorts:
- view_sorts_list: List all sorts for a view
- view_sort_get: Get a single sort
- view_sort_create: Create a new sort
- view_sort_update: Update a sort
- view_sort_delete: Delete a sort (requires confirm=True)
"""

from typing import Optional

from ..server import mcp
from ..dependencies import get_client
from ..errors import wrap_api_error
from ..models import ViewSortsListResult, ViewSortResult, ViewSortDeleteResult


@mcp.tool
@wrap_api_error
def view_sorts_list(view_id: str) -> ViewSortsListResult:
    """List all sorts for a view.

    Args:
        view_id: The view ID (e.g., "vw_xxx")

    Returns:
        ViewSortsListResult with list of sorts.
    """
    client = get_client()

    result = client.view_sorts_list(view_id)
    sorts = result.get("sorts", result.get("list", []))

    return ViewSortsListResult(sorts=sorts)


@mcp.tool
@wrap_api_error
def view_sort_get(sort_id: str) -> ViewSortResult:
    """Get details of a single sort.

    Args:
        sort_id: The sort ID (e.g., "srt_xxx")

    Returns:
        ViewSortResult with sort details.
    """
    client = get_client()

    result = client.view_sort_get(sort_id)

    return ViewSortResult(
        id=result.get("id", sort_id),
        fk_column_id=result.get("fk_column_id", ""),
        direction=result.get("direction", "asc"),
    )


@mcp.tool
@wrap_api_error
def view_sort_create(
    view_id: str,
    fk_column_id: str,
    direction: str = "asc",
) -> ViewSortResult:
    """Create a new sort for a view.

    Args:
        view_id: The view ID (e.g., "vw_xxx")
        fk_column_id: The column/field ID to sort by (e.g., "fld_xxx")
        direction: Sort direction - "asc" (ascending) or "desc" (descending)

    Returns:
        ViewSortResult with created sort details.
    """
    client = get_client()

    body = {
        "fk_column_id": fk_column_id,
        "direction": direction,
    }

    result = client.view_sort_create(view_id, body)

    return ViewSortResult(
        id=result.get("id", ""),
        fk_column_id=result.get("fk_column_id", fk_column_id),
        direction=result.get("direction", direction),
    )


@mcp.tool
@wrap_api_error
def view_sort_update(
    sort_id: str,
    fk_column_id: Optional[str] = None,
    direction: Optional[str] = None,
) -> ViewSortResult:
    """Update an existing sort.

    Args:
        sort_id: The sort ID (e.g., "srt_xxx")
        fk_column_id: New column/field ID
        direction: New sort direction - "asc" or "desc"

    Returns:
        ViewSortResult with updated sort details.
    """
    client = get_client()

    body = {}
    if fk_column_id is not None:
        body["fk_column_id"] = fk_column_id
    if direction is not None:
        body["direction"] = direction

    if not body:
        from fastmcp.exceptions import ToolError
        raise ToolError("At least one field (fk_column_id or direction) must be provided")

    result = client.view_sort_update(sort_id, body)

    return ViewSortResult(
        id=result.get("id", sort_id),
        fk_column_id=result.get("fk_column_id", ""),
        direction=result.get("direction", "asc"),
    )


@mcp.tool(annotations={
    "title": "Delete Sort",
    "destructiveHint": True,
    "idempotentHint": True,
})
@wrap_api_error
def view_sort_delete(
    sort_id: str,
    confirm: bool = False,
) -> ViewSortDeleteResult:
    """Delete a sort from a view.

    Args:
        sort_id: The sort ID (e.g., "srt_xxx")
        confirm: Must be True to proceed with deletion

    Returns:
        ViewSortDeleteResult with success status.
    """
    if not confirm:
        from fastmcp.exceptions import ToolError
        raise ToolError(
            "Set confirm=True to delete this sort."
        )

    client = get_client()

    client.view_sort_delete(sort_id)

    return ViewSortDeleteResult(
        success=True,
        message=f"Sort {sort_id} deleted",
    )
