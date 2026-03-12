"""Tables tools for NocoDB MCP server.

Provides CRUD operations for tables:
- tables_list: List all tables in the base
- table_get: Get table details with fields
- table_create: Create a new table
- table_update: Update table metadata
- table_delete: Delete a table (requires confirm=True)
"""

from typing import Optional, Any

from ..server import mcp
from ..dependencies import get_client, get_base_id
from ..errors import wrap_api_error
from ..models import TablesListResult, TableResult, TableDeleteResult


@mcp.tool
@wrap_api_error
def tables_list() -> TablesListResult:
    """List all tables in the current base.

    Returns:
        TablesListResult with list of tables including id, title, and type.
    """
    client = get_client()
    base_id = get_base_id()

    result = client.tables_list_v3(base_id)
    tables = result.get("list", [])

    return TablesListResult(tables=tables)


@mcp.tool
@wrap_api_error
def table_get(table_id: str) -> TableResult:
    """Get detailed information about a table including its fields.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")

    Returns:
        TableResult with id, title, fields, and metadata.
    """
    client = get_client()
    base_id = get_base_id()

    result = client.table_read_v3(base_id, table_id)

    return TableResult(
        id=result.get("id", table_id),
        title=result.get("title", ""),
        fields=result.get("fields", []),
        meta=result.get("meta"),
    )


@mcp.tool
@wrap_api_error
def table_create(
    title: str,
    fields: Optional[list[dict[str, Any]]] = None,
) -> TableResult:
    """Create a new table in the current base.

    Args:
        title: The table title (e.g., "Users", "Tasks")
        fields: Optional list of field definitions to create with the table.
            Each field should have "title" and "type" keys.
            Example: [{"title": "Name", "type": "SingleLineText"}, {"title": "Email", "type": "Email"}]

    Returns:
        TableResult with created table details.

    Field types:
        - SingleLineText: Short text
        - LongText: Multi-line text
        - Number: Integer
        - Decimal: Float (options: {"precision": 2})
        - Email: Email address
        - URL: Web link
        - PhoneNumber: Phone
        - Date: Date only
        - DateTime: Date + time
        - Checkbox: Boolean
        - SingleSelect: Dropdown (options: {"options": {"choices": [{"title": "A"}]}})
        - MultiSelect: Multi-dropdown
        - Rating: Star rating
        - Attachment: File upload
        - Links: Relationship to another table
    """
    client = get_client()
    base_id = get_base_id()

    body: dict[str, Any] = {"title": title}
    if fields:
        body["fields"] = fields

    result = client.table_create_v3(base_id, body)

    return TableResult(
        id=result.get("id", ""),
        title=result.get("title", title),
        fields=result.get("fields", []),
        meta=result.get("meta"),
    )


@mcp.tool
@wrap_api_error
def table_update(
    table_id: str,
    title: Optional[str] = None,
    icon: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> TableResult:
    """Update a table's metadata.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        title: New table title
        icon: Table icon (emoji, e.g., "🎯")
        meta: Additional metadata dict

    Returns:
        TableResult with updated table details.
    """
    client = get_client()
    base_id = get_base_id()

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

    result = client.table_update_v3(base_id, table_id, body)

    return TableResult(
        id=result.get("id", table_id),
        title=result.get("title", ""),
        fields=result.get("fields", []),
        meta=result.get("meta"),
    )


@mcp.tool(annotations={
    "title": "Delete Table",
    "destructiveHint": True,
    "idempotentHint": False,
})
@wrap_api_error
def table_delete(
    table_id: str,
    confirm: bool = False,
) -> TableDeleteResult:
    """Delete a table and all its data.

    DESTRUCTIVE: This permanently deletes the table, all its fields,
    and ALL RECORDS. This cannot be undone. Set confirm=True to proceed.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        confirm: Must be True to proceed with deletion

    Returns:
        TableDeleteResult with success status.
    """
    if not confirm:
        from fastmcp.exceptions import ToolError
        raise ToolError(
            "Set confirm=True to delete this table. "
            "This permanently deletes the table and ALL its records."
        )

    client = get_client()
    base_id = get_base_id()

    client.table_delete_v3(base_id, table_id)

    return TableDeleteResult(
        success=True,
        message=f"Table {table_id} deleted",
    )
