"""Attachments tool for NocoDB MCP server.

Provides file attachment upload to record fields:
- attachment_upload: Upload a file to an Attachment field on a record
"""

import base64

from ..server import mcp
from ..dependencies import get_client, get_base_id
from ..errors import wrap_api_error
from ..models import AttachmentUploadResult


@mcp.tool
@wrap_api_error
def attachment_upload(
    table_id: str,
    record_id: str,
    field_id: str,
    filename: str,
    content_base64: str,
    content_type: str,
) -> AttachmentUploadResult:
    """Upload a file attachment to a record's Attachment field.

    The file content must be provided as base64-encoded data.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        record_id: The record ID to attach the file to
        field_id: The Attachment field ID (e.g., "fld_xxx")
        filename: The filename for the uploaded file (e.g., "document.pdf")
        content_base64: Base64-encoded file content
        content_type: MIME type of the file (e.g., "application/pdf", "image/png")

    Returns:
        AttachmentUploadResult with URL and metadata.

    Example:
        # Upload a small text file
        import base64
        content = base64.b64encode(b"Hello World").decode()
        attachment_upload("tbl_xxx", "1", "fld_attach", "hello.txt", content, "text/plain")

    Common MIME types:
        - application/pdf
        - image/png, image/jpeg, image/gif
        - text/plain, text/csv
        - application/json
        - application/vnd.openxmlformats-officedocument.spreadsheetml.sheet (xlsx)
    """
    client = get_client()
    base_id = get_base_id()

    # Decode base64 to bytes
    try:
        content_bytes = base64.b64decode(content_base64)
    except Exception as e:
        from fastmcp.exceptions import ToolError
        raise ToolError(f"Invalid base64 content: {e}")

    result = client.attachment_upload_v3(
        base_id, table_id, record_id, field_id,
        filename=filename,
        content=content_bytes,
        content_type=content_type,
    )

    return AttachmentUploadResult(
        url=result.get("url", ""),
        title=result.get("title", filename),
        mimetype=result.get("mimetype", content_type),
        size=result.get("size"),
    )
