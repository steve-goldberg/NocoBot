"""Storage tool for NocoDB MCP server.

Provides general file storage operations:
- storage_upload: Upload a file to NocoDB storage

This is for general file uploads, not record-attached attachments.
Use attachment_upload for attaching files to specific records.
"""

import base64
from typing import Optional

from ..server import mcp
from ..dependencies import get_client
from ..errors import wrap_api_error
from ..models import StorageUploadResult


@mcp.tool
@wrap_api_error
def storage_upload(
    filename: str,
    content_base64: str,
    content_type: Optional[str] = None,
) -> StorageUploadResult:
    """Upload a file to NocoDB general storage.

    This uploads a file to storage without attaching it to a specific record.
    Useful for assets that need to be referenced across multiple records.

    Args:
        filename: The filename (e.g., "logo.png", "document.pdf")
        content_base64: Base64-encoded file content
        content_type: Optional MIME type (auto-detected if not provided)

    Returns:
        StorageUploadResult with URL and metadata.

    For attaching files to specific record fields, use attachment_upload instead.

    Common MIME types:
        - application/pdf
        - image/png, image/jpeg, image/gif
        - text/plain, text/csv
        - application/json
    """
    client = get_client()

    # Decode base64 to bytes
    try:
        content_bytes = base64.b64decode(content_base64)
    except Exception as e:
        from fastmcp.exceptions import ToolError
        raise ToolError(f"Invalid base64 content: {e}")

    result = client.storage_upload(
        filename=filename,
        content=content_bytes,
        content_type=content_type,
    )

    return StorageUploadResult(
        url=result.get("url", ""),
        title=result.get("title", filename),
        mimetype=result.get("mimetype", content_type or "application/octet-stream"),
    )
