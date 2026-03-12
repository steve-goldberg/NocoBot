"""Export tool for NocoDB MCP server.

Provides data export operations:
- export_csv: Export a view's data as CSV
"""

from typing import Optional

from ..server import mcp
from ..dependencies import get_client, get_base_id
from ..errors import wrap_api_error
from ..models import ExportResult


@mcp.tool
@wrap_api_error
def export_csv(
    view_id: str,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> ExportResult:
    """Export a view's data as CSV.

    Args:
        view_id: The view ID (e.g., "vw_xxx")
        offset: Row offset for pagination (skip first N rows)
        limit: Maximum number of rows to export

    Returns:
        ExportResult with CSV content as a string.

    Note: For large datasets, use offset and limit for pagination
    to avoid timeouts.

    Example:
        # Export first 100 rows
        export_csv("vw_xxx", limit=100)

        # Export rows 101-200
        export_csv("vw_xxx", offset=100, limit=100)
    """
    client = get_client()
    base_id = get_base_id()

    csv_bytes = client.export_view(
        base_id, view_id,
        offset=offset,
        limit=limit,
    )

    # Decode bytes to string
    csv_content = csv_bytes.decode("utf-8")

    # Count rows (subtract 1 for header)
    row_count = csv_content.count("\n")
    if row_count > 0:
        row_count -= 1  # Don't count header row

    return ExportResult(
        csv_content=csv_content,
        row_count=row_count if row_count > 0 else None,
    )
