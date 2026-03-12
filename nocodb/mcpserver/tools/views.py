"""Views tools for NocoDB MCP server.

Provides operations for table views:
- views_list: List all views for a table
- view_update: Update view metadata
- view_delete: Delete a view (requires confirm=True)

Note: View creation is not available via API in self-hosted NocoDB.
Use the NocoDB web UI to create new views.
"""

from typing import Optional, Any

from ..server import mcp
from ..dependencies import get_client
from ..errors import wrap_api_error
from ..models import ViewsListResult, ViewResult, ViewDeleteResult


@mcp.tool
@wrap_api_error
def views_list(table_id: str) -> ViewsListResult:
    """List all views for a table.

    Views include Grid, Gallery, Form, Kanban, and Calendar views.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")

    Returns:
        ViewsListResult with list of views including id, title, and type.

    View types (numeric):
        - 3: Grid
        - 4: Form
        - 5: Gallery
        - 6: Kanban
        - 7: Calendar
    """
    client = get_client()

    result = client.views_list(table_id)
    views = result.get("list", [])

    return ViewsListResult(views=views)


@mcp.tool
@wrap_api_error
def view_update(
    view_id: str,
    title: Optional[str] = None,
    icon: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> ViewResult:
    """Update a view's metadata.

    Args:
        view_id: The view ID (e.g., "vw_xxx")
        title: New view title
        icon: View icon (emoji, e.g., "📊")
        meta: Additional metadata dict

    Returns:
        ViewResult with updated view details.
    """
    client = get_client()

    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    if icon is not None:
        body["icon"] = icon
    if meta is not None:
        body["meta"] = meta

    if not body:
        from fastmcp.exceptions import ToolError
        raise ToolError("At least one field (title, icon, or meta) must be provided")

    result = client.view_update(view_id, body)

    return ViewResult(
        id=result.get("id", view_id),
        title=result.get("title", ""),
        type=result.get("type", 0),
        meta=result.get("meta"),
    )


@mcp.tool(annotations={
    "title": "Delete View",
    "destructiveHint": True,
    "idempotentHint": False,
})
@wrap_api_error
def view_delete(
    view_id: str,
    confirm: bool = False,
) -> ViewDeleteResult:
    """Delete a view.

    This only deletes the view, not the underlying data.
    Records remain intact.

    Args:
        view_id: The view ID (e.g., "vw_xxx")
        confirm: Must be True to proceed with deletion

    Returns:
        ViewDeleteResult with success status.
    """
    if not confirm:
        from fastmcp.exceptions import ToolError
        raise ToolError(
            "Set confirm=True to delete this view. "
            "The view will be removed but data remains intact."
        )

    client = get_client()

    client.view_delete(view_id)

    return ViewDeleteResult(
        success=True,
        message=f"View {view_id} deleted",
    )
