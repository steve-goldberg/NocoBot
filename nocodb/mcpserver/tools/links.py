"""Links tools for NocoDB MCP server.

Provides operations for linked records (relationships):
- linked_records_list: List records linked to a specific record
- linked_records_link: Link records together
- linked_records_unlink: Unlink records (requires confirm=True)
"""

from typing import Optional

from ..server import mcp
from ..dependencies import get_client, get_base_id
from ..errors import wrap_api_error
from ..models import LinkedRecordsResult


@mcp.tool
@wrap_api_error
def linked_records_list(
    table_id: str,
    link_field_id: str,
    record_id: str,
    fields: Optional[str] = None,
    sort: Optional[str] = None,
    where: Optional[str] = None,
) -> LinkedRecordsResult:
    """List records linked to a specific record via a Links field.

    Args:
        table_id: The table ID containing the link field (e.g., "tbl_xxx")
        link_field_id: The Links field ID (e.g., "fld_xxx")
        record_id: The record ID to get linked records for
        fields: Comma-separated field names to include from linked records
        sort: Sort field(s), prefix with - for descending
        where: Filter condition for linked records

    Returns:
        LinkedRecordsResult with linked records.

    Example:
        # Get all tasks linked to a project
        linked_records_list("tbl_projects", "fld_tasks_link", "1")
    """
    client = get_client()
    base_id = get_base_id()

    params = {}
    if fields:
        params["fields"] = fields
    if sort:
        params["sort"] = sort
    if where:
        params["where"] = where

    result = client.linked_records_list_v3(
        base_id, table_id, link_field_id, record_id,
        params=params if params else None
    )

    # Response format varies by relationship type
    # hm (has many): {"list": [...]} or {"records": [...]}
    # bt (belongs to): {"record": {...}} (singular)
    records = result.get("records", result.get("list", []))
    if isinstance(records, dict):
        # belongs_to returns single record
        records = [records] if records else []

    has_next = "next" in result and bool(result["next"])

    return LinkedRecordsResult(records=records, has_next=has_next)


@mcp.tool
@wrap_api_error
def linked_records_link(
    table_id: str,
    link_field_id: str,
    record_id: str,
    target_ids: list[str],
) -> LinkedRecordsResult:
    """Link records together via a Links field.

    Creates a relationship between the source record and target records.

    Args:
        table_id: The table ID containing the link field (e.g., "tbl_xxx")
        link_field_id: The Links field ID (e.g., "fld_xxx")
        record_id: The source record ID to link from
        target_ids: List of record IDs to link to (e.g., ["1", "2", "3"])

    Returns:
        LinkedRecordsResult with linked record references.

    Example:
        # Link tasks 1, 2, 3 to project 5
        linked_records_link("tbl_projects", "fld_tasks_link", "5", ["1", "2", "3"])
    """
    client = get_client()
    base_id = get_base_id()

    result = client.linked_records_link_v3(
        base_id, table_id, link_field_id, record_id, target_ids
    )

    # Result is list of {"id": ...} for linked records
    records = result if isinstance(result, list) else []

    return LinkedRecordsResult(records=records)


@mcp.tool(annotations={
    "title": "Unlink Records",
    "destructiveHint": True,
    "idempotentHint": True,
})
@wrap_api_error
def linked_records_unlink(
    table_id: str,
    link_field_id: str,
    record_id: str,
    target_ids: list[str],
    confirm: bool = False,
) -> LinkedRecordsResult:
    """Unlink records from a Links field relationship.

    Removes the relationship between records. Does NOT delete the records themselves.

    DESTRUCTIVE: Set confirm=True to proceed.

    Args:
        table_id: The table ID containing the link field (e.g., "tbl_xxx")
        link_field_id: The Links field ID (e.g., "fld_xxx")
        record_id: The source record ID to unlink from
        target_ids: List of record IDs to unlink (e.g., ["1", "2"])
        confirm: Must be True to proceed with unlinking

    Returns:
        LinkedRecordsResult with unlinked record references.

    Example:
        # Unlink task 2 from project 5
        linked_records_unlink("tbl_projects", "fld_tasks_link", "5", ["2"], confirm=True)
    """
    if not confirm:
        from fastmcp.exceptions import ToolError
        raise ToolError(
            "Set confirm=True to unlink records. "
            "This removes the relationship but does not delete the records."
        )

    client = get_client()
    base_id = get_base_id()

    result = client.linked_records_unlink_v3(
        base_id, table_id, link_field_id, record_id, target_ids
    )

    # Result is list of {"id": ...} for unlinked records
    records = result if isinstance(result, list) else []

    return LinkedRecordsResult(records=records)
