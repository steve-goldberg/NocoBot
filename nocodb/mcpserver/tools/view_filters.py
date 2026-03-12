"""View filters tools for NocoDB MCP server.

Provides CRUD operations for view filters:
- view_filters_list: List all filters for a view
- view_filter_get: Get a single filter
- view_filter_create: Create a new filter
- view_filter_update: Update a filter
- view_filter_delete: Delete a filter (requires confirm=True)
- view_filter_children: Get children of a filter group
"""

from typing import Optional, Any

from ..server import mcp
from ..dependencies import get_client
from ..errors import wrap_api_error
from ..models import ViewFiltersListResult, ViewFilterResult, ViewFilterDeleteResult


@mcp.tool
@wrap_api_error
def view_filters_list(view_id: str) -> ViewFiltersListResult:
    """List all filters for a view.

    Args:
        view_id: The view ID (e.g., "vw_xxx")

    Returns:
        ViewFiltersListResult with list of filters.
    """
    client = get_client()

    result = client.view_filters_list(view_id)
    filters = result.get("list", [])

    return ViewFiltersListResult(filters=filters)


@mcp.tool
@wrap_api_error
def view_filter_get(filter_id: str) -> ViewFilterResult:
    """Get details of a single filter.

    Args:
        filter_id: The filter ID (e.g., "flt_xxx")

    Returns:
        ViewFilterResult with filter details.
    """
    client = get_client()

    result = client.view_filter_get(filter_id)

    return ViewFilterResult(
        id=result.get("id", filter_id),
        fk_column_id=result.get("fk_column_id", ""),
        comparison_op=result.get("comparison_op", ""),
        value=result.get("value"),
    )


@mcp.tool
@wrap_api_error
def view_filter_create(
    view_id: str,
    fk_column_id: str,
    comparison_op: str,
    value: Any = None,
) -> ViewFilterResult:
    """Create a new filter for a view.

    Args:
        view_id: The view ID (e.g., "vw_xxx")
        fk_column_id: The column/field ID to filter on (e.g., "fld_xxx")
        comparison_op: The comparison operator
        value: The filter value (not needed for null/empty checks)

    Returns:
        ViewFilterResult with created filter details.

    Comparison operators:
        - eq: Equal
        - neq: Not equal
        - like: Contains (use % wildcards)
        - nlike: Does not contain
        - gt: Greater than
        - lt: Less than
        - gte: Greater than or equal
        - lte: Less than or equal
        - is: Is null/notnull
        - isnot: Is not null
        - empty: Is empty
        - notempty: Is not empty
        - in: In array (comma-separated values)
        - notin: Not in array

    Examples:
        - view_filter_create("vw_xxx", "fld_status", "eq", "Active")
        - view_filter_create("vw_xxx", "fld_age", "gt", 18)
        - view_filter_create("vw_xxx", "fld_email", "is", "notnull")
    """
    client = get_client()

    body: dict[str, Any] = {
        "fk_column_id": fk_column_id,
        "comparison_op": comparison_op,
    }
    if value is not None:
        body["value"] = value

    result = client.view_filter_create(view_id, body)

    return ViewFilterResult(
        id=result.get("id", ""),
        fk_column_id=result.get("fk_column_id", fk_column_id),
        comparison_op=result.get("comparison_op", comparison_op),
        value=result.get("value", value),
    )


@mcp.tool
@wrap_api_error
def view_filter_update(
    filter_id: str,
    fk_column_id: Optional[str] = None,
    comparison_op: Optional[str] = None,
    value: Any = None,
) -> ViewFilterResult:
    """Update an existing filter.

    Args:
        filter_id: The filter ID (e.g., "flt_xxx")
        fk_column_id: New column/field ID
        comparison_op: New comparison operator
        value: New filter value

    Returns:
        ViewFilterResult with updated filter details.
    """
    client = get_client()

    body: dict[str, Any] = {}
    if fk_column_id is not None:
        body["fk_column_id"] = fk_column_id
    if comparison_op is not None:
        body["comparison_op"] = comparison_op
    if value is not None:
        body["value"] = value

    if not body:
        from fastmcp.exceptions import ToolError
        raise ToolError("At least one field must be provided to update")

    result = client.view_filter_update(filter_id, body)

    return ViewFilterResult(
        id=result.get("id", filter_id),
        fk_column_id=result.get("fk_column_id", ""),
        comparison_op=result.get("comparison_op", ""),
        value=result.get("value"),
    )


@mcp.tool(annotations={
    "title": "Delete Filter",
    "destructiveHint": True,
    "idempotentHint": True,
})
@wrap_api_error
def view_filter_delete(
    filter_id: str,
    confirm: bool = False,
) -> ViewFilterDeleteResult:
    """Delete a filter from a view.

    Args:
        filter_id: The filter ID (e.g., "flt_xxx")
        confirm: Must be True to proceed with deletion

    Returns:
        ViewFilterDeleteResult with success status.
    """
    if not confirm:
        from fastmcp.exceptions import ToolError
        raise ToolError(
            "Set confirm=True to delete this filter."
        )

    client = get_client()

    client.view_filter_delete(filter_id)

    return ViewFilterDeleteResult(
        success=True,
        message=f"Filter {filter_id} deleted",
    )


@mcp.tool
@wrap_api_error
def view_filter_children(filter_group_id: str) -> ViewFiltersListResult:
    """Get children filters of a filter group.

    Filter groups allow nested AND/OR logic.

    Args:
        filter_group_id: The parent filter group ID

    Returns:
        ViewFiltersListResult with child filters.
    """
    client = get_client()

    result = client.view_filter_children(filter_group_id)
    filters = result.get("list", result.get("children", []))

    return ViewFiltersListResult(filters=filters)
