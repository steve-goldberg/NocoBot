"""Schema export tools for NocoDB MCP server.

Provides tools to export portable schemas:
- schema_export_table: Export a single table's schema
- schema_export_base: Export entire base schema with all tables
"""

from ..server import mcp
from ..dependencies import get_client, get_base_id
from ..errors import wrap_api_error
from ..models import TableSchemaResult, BaseSchemaResult
from ...schema_utils import extract_portable_table_schema, extract_portable_base_schema


@mcp.tool
@wrap_api_error
def schema_export_table(table_id: str) -> TableSchemaResult:
    """Export portable schema for a single table.

    Returns a clean schema with system fields and internal IDs removed,
    suitable for documentation or recreating the table structure.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")

    Returns:
        TableSchemaResult with title and fields array.
        Each field contains type, title, and field-specific options.

    Example output:
        {
            "title": "Users",
            "fields": [
                {"title": "Name", "type": "SingleLineText"},
                {"title": "Email", "type": "Email"},
                {"title": "Status", "type": "SingleSelect", "colOptions": {...}}
            ]
        }
    """
    client = get_client()
    base_id = get_base_id()

    # Fetch full table metadata
    table_data = client.table_read_v3(base_id, table_id)

    # Convert to portable format
    schema = extract_portable_table_schema(table_data)

    return TableSchemaResult(
        title=schema["title"],
        fields=schema["fields"],
    )


@mcp.tool
@wrap_api_error
def schema_export_base() -> BaseSchemaResult:
    """Export portable schema for the entire base with all tables.

    Returns a clean schema with system fields and internal IDs removed,
    suitable for documentation or recreating the base structure.

    Returns:
        BaseSchemaResult with title, description, and tables array.
        Each table contains title and fields array.

    Example output:
        {
            "title": "My Project",
            "description": "Project database",
            "tables": [
                {
                    "title": "Users",
                    "fields": [...]
                },
                {
                    "title": "Tasks",
                    "fields": [...]
                }
            ]
        }
    """
    client = get_client()
    base_id = get_base_id()

    # Fetch base metadata
    base_data = client.base_read(base_id)

    # Get list of all tables
    tables_response = client.tables_list_v3(base_id)
    tables_list = tables_response.get("list", [])

    # Fetch full schema for each table
    tables_data = []
    for table in tables_list:
        table_id = table["id"]
        table_data = client.table_read_v3(base_id, table_id)
        tables_data.append(table_data)

    # Convert to portable format
    schema = extract_portable_base_schema(base_data, tables_data)

    return BaseSchemaResult(
        title=schema["title"],
        tables=schema["tables"],
        description=schema.get("description"),
    )
