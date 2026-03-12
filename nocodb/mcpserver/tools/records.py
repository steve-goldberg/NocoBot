"""Records tools for NocoDB MCP server.

Provides CRUD operations for table records:
- records_list: List records with filtering/pagination
- records_list_all: Fetch all records across pages
- record_get: Get a single record
- records_create: Create one or more records
- records_update: Update records
- records_delete: Delete records (requires confirm=True)
- records_count: Count records matching filter
"""

from typing import Optional

from ..server import mcp
from ..dependencies import get_client, get_base_id
from ..errors import wrap_api_error
from ..models import (
    RecordsListResult,
    RecordResult,
    RecordsCountResult,
    RecordsMutationResult,
)


@mcp.tool
@wrap_api_error
def records_list(
    table_id: str,
    fields: Optional[str] = None,
    sort: Optional[str] = None,
    where: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
    view_id: Optional[str] = None,
) -> RecordsListResult:
    """List records from a table with optional filtering and pagination.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        fields: Comma-separated field names to include (e.g., "Name,Email,Status")
        sort: Sort field(s), prefix with - for descending (e.g., "-CreatedAt" or "Name,-Age")
        where: Filter condition using NocoDB syntax (e.g., "(Status,eq,Active)")
        page: Page number (1-indexed, default: 1)
        page_size: Records per page (default: 25, max: 1000)
        view_id: Optional view ID to filter by

    Returns:
        RecordsListResult with records array and pagination info.

    Filter syntax examples:
        - Equal: (Status,eq,Active)
        - Not equal: (Status,neq,Deleted)
        - Like: (Name,like,%john%)
        - Greater than: (Age,gt,18)
        - Is null: (Email,is,null)
        - Multiple: (Status,eq,Active)~and(Priority,eq,High)
    """
    client = get_client()
    base_id = get_base_id()

    params = {"page": page, "pageSize": page_size}
    if fields:
        params["fields"] = fields
    if sort:
        params["sort"] = sort
    if where:
        params["where"] = where
    if view_id:
        params["viewId"] = view_id

    result = client.records_list_v3(base_id, table_id, params=params)

    records = result.get("records", [])
    has_next = "next" in result and bool(result["next"])

    return RecordsListResult(
        records=records,
        page=page,
        page_size=page_size,
        has_next=has_next,
    )


@mcp.tool
@wrap_api_error
def records_list_all(
    table_id: str,
    where: Optional[str] = None,
    page_size: int = 100,
    max_pages: Optional[int] = None,
) -> list[dict]:
    """Fetch all records from a table, automatically handling pagination.

    Use with caution on large tables. Consider using records_list with
    pagination for better control.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        where: Optional filter condition
        page_size: Records per page (default: 100)
        max_pages: Maximum pages to fetch (None = unlimited)

    Returns:
        List of all matching records.
    """
    client = get_client()
    base_id = get_base_id()

    params = {"pageSize": page_size}
    if where:
        params["where"] = where

    return client.records_list_all_v3(base_id, table_id, params=params, max_pages=max_pages)


@mcp.tool
@wrap_api_error
def record_get(
    table_id: str,
    record_id: str,
) -> RecordResult:
    """Get a single record by ID.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        record_id: The record ID (e.g., "1" or "rec_xxx")

    Returns:
        RecordResult with id and fields.
    """
    client = get_client()
    base_id = get_base_id()

    result = client.record_get_v3(base_id, table_id, record_id)

    return RecordResult(
        id=result.get("id"),
        fields=result.get("fields", {}),
    )


@mcp.tool
@wrap_api_error
def records_create(
    table_id: str,
    records: list[dict],
) -> RecordsMutationResult:
    """Create one or more records in a table.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        records: List of record data dicts. Each dict should contain field values.
            Example: [{"Name": "John", "Email": "john@example.com"}]
            For batch: [{"Name": "A"}, {"Name": "B"}, {"Name": "C"}]

    Returns:
        RecordsMutationResult with created records.
    """
    client = get_client()
    base_id = get_base_id()

    # Wrap each record in {"fields": ...} format for v3 API
    formatted = [{"fields": r} for r in records]

    result = client.records_create_v3(base_id, table_id, formatted)

    return RecordsMutationResult(
        success=True,
        records=result,
        message=f"Created {len(result)} record(s)",
    )


@mcp.tool
@wrap_api_error
def records_update(
    table_id: str,
    records: list[dict],
) -> RecordsMutationResult:
    """Update one or more records in a table.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        records: List of record updates. Each dict must have "id" and field values.
            Example: [{"id": 1, "Status": "Done"}]
            For batch: [{"id": 1, "Status": "A"}, {"id": 2, "Status": "B"}]

    Returns:
        RecordsMutationResult with updated records.
    """
    client = get_client()
    base_id = get_base_id()

    # Format records for v3 API: {"id": x, "fields": {...}}
    formatted = []
    for r in records:
        record_id = r.pop("id", None)
        if record_id is None:
            raise ValueError("Each record must have an 'id' field")
        formatted.append({"id": record_id, "fields": r})

    result = client.records_update_v3(base_id, table_id, formatted)

    return RecordsMutationResult(
        success=True,
        records=result,
        message=f"Updated {len(result)} record(s)",
    )


@mcp.tool(annotations={
    "title": "Delete Records",
    "destructiveHint": True,
    "idempotentHint": False,
})
@wrap_api_error
def records_delete(
    table_id: str,
    record_ids: list[str],
    confirm: bool = False,
) -> RecordsMutationResult:
    """Delete one or more records from a table.

    DESTRUCTIVE: This operation cannot be undone. Set confirm=True to proceed.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        record_ids: List of record IDs to delete (e.g., ["1", "2", "3"])
        confirm: Must be True to proceed with deletion

    Returns:
        RecordsMutationResult with deleted record IDs.
    """
    if not confirm:
        from fastmcp.exceptions import ToolError
        raise ToolError(
            "Set confirm=True to delete records. "
            "This is a destructive operation that cannot be undone."
        )

    client = get_client()
    base_id = get_base_id()

    result = client.records_delete_v3(base_id, table_id, record_ids)

    return RecordsMutationResult(
        success=True,
        records=result,
        message=f"Deleted {len(result)} record(s)",
    )


@mcp.tool
@wrap_api_error
def records_count(
    table_id: str,
    where: Optional[str] = None,
) -> RecordsCountResult:
    """Count records in a table, optionally filtered.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        where: Optional filter condition (e.g., "(Status,eq,Active)")

    Returns:
        RecordsCountResult with count.
    """
    client = get_client()
    base_id = get_base_id()

    params = {}
    if where:
        params["where"] = where

    result = client.records_count_v3(base_id, table_id, params=params if params else None)

    return RecordsCountResult(count=result.get("count", 0))
