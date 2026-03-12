"""Fields tools for NocoDB MCP server.

Provides CRUD operations for table fields (columns):
- fields_list: List all fields in a table
- field_get: Get field details
- field_create: Create a new field
- field_update: Update field metadata
- field_update_options: Update field colOptions (v2 API for colors)
- field_delete: Delete a field (requires confirm=True)
"""

from typing import Optional, Any

from ..server import mcp
from ..dependencies import get_client, get_base_id
from ..errors import wrap_api_error
from ..models import FieldsListResult, FieldResult, FieldDeleteResult


@mcp.tool
@wrap_api_error
def fields_list(table_id: str) -> FieldsListResult:
    """List all fields in a table.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")

    Returns:
        FieldsListResult with list of fields including id, title, type, and options.
    """
    client = get_client()
    base_id = get_base_id()

    result = client.fields_list_v3(base_id, table_id)
    fields = result.get("list", [])

    return FieldsListResult(fields=fields)


@mcp.tool
@wrap_api_error
def field_get(field_id: str) -> FieldResult:
    """Get detailed information about a field.

    Args:
        field_id: The field ID (e.g., "fld_xxx")

    Returns:
        FieldResult with id, title, type, and options.
    """
    client = get_client()
    base_id = get_base_id()

    result = client.field_read_v3(base_id, field_id)

    return FieldResult(
        id=result.get("id", field_id),
        title=result.get("title", ""),
        type=result.get("uidt", result.get("type", "")),
        options=result.get("colOptions") or result.get("options"),
    )


@mcp.tool
@wrap_api_error
def field_create(
    table_id: str,
    title: str,
    field_type: str,
    options: Optional[dict[str, Any]] = None,
) -> FieldResult:
    """Create a new field in a table.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        title: The field title (e.g., "Status", "Email")
        field_type: The field type (see list below)
        options: Optional field-specific options

    Returns:
        FieldResult with created field details.

    Field types:
        - SingleLineText: Short text
        - LongText: Multi-line text
        - Number: Integer
        - Decimal: Float (options: {"precision": 2})
        - Currency: Money (options: {"locale": "en-US", "code": "USD"})
        - Percent: Percentage
        - Email: Email address
        - URL: Web link
        - PhoneNumber: Phone
        - Date: Date only (options: {"date_format": "YYYY-MM-DD"})
        - DateTime: Date + time
        - Time: Time only
        - Duration: Time span
        - Checkbox: Boolean
        - SingleSelect: Dropdown
            options: {"options": {"choices": [{"title": "A", "color": "#00FF00"}]}}
        - MultiSelect: Multi-dropdown (same options as SingleSelect)
        - Rating: Star rating (options: {"max": 5})
        - Attachment: File upload
        - Links: Relationship
            options: {"relation_type": "hm", "related_table_id": "tbl_xxx"}
            relation_type: "hm" (has many), "bt" (belongs to), "mm" (many to many)
        - Lookup: Related field value
        - Rollup: Aggregation of related records
        - Formula: Calculated field (options: {"formula": "..."})

    SingleSelect/MultiSelect colors: Use HEX codes like "#00FF00", not color names.
    """
    client = get_client()
    base_id = get_base_id()

    body: dict[str, Any] = {
        "title": title,
        "type": field_type,
    }
    if options:
        body["options"] = options

    result = client.field_create_v3(base_id, table_id, body)

    return FieldResult(
        id=result.get("id", ""),
        title=result.get("title", title),
        type=result.get("uidt", result.get("type", field_type)),
        options=result.get("colOptions") or result.get("options"),
    )


@mcp.tool
@wrap_api_error
def field_update(
    field_id: str,
    title: Optional[str] = None,
    options: Optional[dict[str, Any]] = None,
) -> FieldResult:
    """Update a field's metadata.

    Note: For updating SingleSelect/MultiSelect colors, use field_update_options instead.

    Args:
        field_id: The field ID (e.g., "fld_xxx")
        title: New field title
        options: New field options (not for colOptions updates)

    Returns:
        FieldResult with updated field details.
    """
    client = get_client()
    base_id = get_base_id()

    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    if options is not None:
        body["options"] = options

    if not body:
        from fastmcp.exceptions import ToolError
        raise ToolError("At least one field (title or options) must be provided")

    result = client.field_update_v3(base_id, field_id, body)

    return FieldResult(
        id=result.get("id", field_id),
        title=result.get("title", ""),
        type=result.get("uidt", result.get("type", "")),
        options=result.get("colOptions") or result.get("options"),
    )


@mcp.tool
@wrap_api_error
def field_update_options(
    field_id: str,
    col_options: dict[str, Any],
) -> FieldResult:
    """Update a field's colOptions using v2 API.

    Use this specifically for updating SingleSelect/MultiSelect choice colors,
    which requires the v2 column update API.

    Args:
        field_id: The field ID (e.g., "fld_xxx")
        col_options: The colOptions dict with updated choices.
            Example for SingleSelect colors:
            {
                "options": [
                    {"id": "opt_xxx", "title": "Active", "color": "#00FF00"},
                    {"id": "opt_yyy", "title": "Inactive", "color": "#FF0000"}
                ]
            }

    Returns:
        FieldResult with updated field details.

    Note: You must include the option "id" for existing options.
    Get the current option IDs using field_get first.
    """
    client = get_client()

    body = {"colOptions": col_options}
    result = client.column_update_v2(field_id, body)

    return FieldResult(
        id=result.get("id", field_id),
        title=result.get("title", ""),
        type=result.get("uidt", result.get("type", "")),
        options=result.get("colOptions") or result.get("options"),
    )


@mcp.tool(annotations={
    "title": "Delete Field",
    "destructiveHint": True,
    "idempotentHint": False,
})
@wrap_api_error
def field_delete(
    field_id: str,
    confirm: bool = False,
) -> FieldDeleteResult:
    """Delete a field from a table.

    DESTRUCTIVE: This permanently deletes the field and ALL DATA in that field
    across all records. This cannot be undone. Set confirm=True to proceed.

    Args:
        field_id: The field ID (e.g., "fld_xxx")
        confirm: Must be True to proceed with deletion

    Returns:
        FieldDeleteResult with success status.
    """
    if not confirm:
        from fastmcp.exceptions import ToolError
        raise ToolError(
            "Set confirm=True to delete this field. "
            "This permanently deletes the field and all its data across all records."
        )

    client = get_client()
    base_id = get_base_id()

    client.field_delete_v3(base_id, field_id)

    return FieldDeleteResult(
        success=True,
        message=f"Field {field_id} deleted",
    )
