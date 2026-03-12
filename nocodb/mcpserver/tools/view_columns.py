"""View columns tools for NocoDB MCP server.

Provides operations for view column visibility:
- view_columns_list: List column visibility settings
- view_column_update: Update a column's visibility/order
- view_columns_hide_all: Hide all columns
- view_columns_show_all: Show all columns
"""

from typing import Optional

from ..server import mcp
from ..dependencies import get_client
from ..errors import wrap_api_error
from ..models import ViewColumnsListResult, ViewColumnResult


@mcp.tool
@wrap_api_error
def view_columns_list(view_id: str) -> ViewColumnsListResult:
    """List all columns in a view with their visibility settings.

    Args:
        view_id: The view ID (e.g., "vw_xxx")

    Returns:
        ViewColumnsListResult with list of columns including show/order settings.
    """
    client = get_client()

    result = client.view_columns_list(view_id)
    columns = result.get("list", [])

    return ViewColumnsListResult(columns=columns)


@mcp.tool
@wrap_api_error
def view_column_update(
    view_id: str,
    column_id: str,
    show: Optional[bool] = None,
    order: Optional[int] = None,
) -> ViewColumnResult:
    """Update a column's visibility or order in a view.

    Args:
        view_id: The view ID (e.g., "vw_xxx")
        column_id: The view column ID (from view_columns_list, not the field ID)
        show: Whether to show (True) or hide (False) the column
        order: Column position (0-indexed)

    Returns:
        ViewColumnResult with updated column settings.
    """
    client = get_client()

    body = {}
    if show is not None:
        body["show"] = show
    if order is not None:
        body["order"] = order

    if not body:
        from fastmcp.exceptions import ToolError
        raise ToolError("At least one field (show or order) must be provided")

    result = client.view_column_update(view_id, column_id, body)

    return ViewColumnResult(
        id=result.get("id", column_id),
        fk_column_id=result.get("fk_column_id", ""),
        show=result.get("show", True),
        order=result.get("order", 0),
    )


@mcp.tool
@wrap_api_error
def view_columns_hide_all(view_id: str) -> ViewColumnsListResult:
    """Hide all columns in a view.

    Useful for starting fresh and then selectively showing specific columns.

    Args:
        view_id: The view ID (e.g., "vw_xxx")

    Returns:
        ViewColumnsListResult with updated column visibility.
    """
    client = get_client()

    client.view_columns_hide_all(view_id)

    # Return updated column list
    result = client.view_columns_list(view_id)
    columns = result.get("list", [])

    return ViewColumnsListResult(columns=columns)


@mcp.tool
@wrap_api_error
def view_columns_show_all(view_id: str) -> ViewColumnsListResult:
    """Show all columns in a view.

    Args:
        view_id: The view ID (e.g., "vw_xxx")

    Returns:
        ViewColumnsListResult with updated column visibility.
    """
    client = get_client()

    client.view_columns_show_all(view_id)

    # Return updated column list
    result = client.view_columns_list(view_id)
    columns = result.get("list", [])

    return ViewColumnsListResult(columns=columns)
