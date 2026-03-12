"""Webhooks tools for NocoDB MCP server.

Provides operations for webhooks:
- webhooks_list: List all webhooks for a table
- webhook_delete: Delete a webhook (requires confirm=True)
- webhook_logs: View webhook execution logs
- webhook_sample_payload: Get sample webhook payload
- webhook_filters_list: List webhook filters
- webhook_filter_create: Create a webhook filter

Note: Webhook creation/update is not available via API in self-hosted NocoDB.
Use the NocoDB web UI to create and configure webhooks.
"""

from typing import Optional, Any

from ..server import mcp
from ..dependencies import get_client
from ..errors import wrap_api_error
from ..models import (
    WebhooksListResult,
    WebhookDeleteResult,
    WebhookLogsResult,
    WebhookSamplePayloadResult,
    WebhookFiltersListResult,
    WebhookFilterResult,
)


@mcp.tool
@wrap_api_error
def webhooks_list(table_id: str) -> WebhooksListResult:
    """List all webhooks for a table.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")

    Returns:
        WebhooksListResult with list of webhooks.
    """
    client = get_client()

    result = client.webhooks_list(table_id)
    webhooks = result.get("list", [])

    return WebhooksListResult(webhooks=webhooks)


@mcp.tool(annotations={
    "title": "Delete Webhook",
    "destructiveHint": True,
    "idempotentHint": False,
})
@wrap_api_error
def webhook_delete(
    hook_id: str,
    confirm: bool = False,
) -> WebhookDeleteResult:
    """Delete a webhook.

    Args:
        hook_id: The webhook ID (e.g., "hk_xxx")
        confirm: Must be True to proceed with deletion

    Returns:
        WebhookDeleteResult with success status.
    """
    if not confirm:
        from fastmcp.exceptions import ToolError
        raise ToolError(
            "Set confirm=True to delete this webhook."
        )

    client = get_client()

    client.webhook_delete(hook_id)

    return WebhookDeleteResult(
        success=True,
        message=f"Webhook {hook_id} deleted",
    )


@mcp.tool
@wrap_api_error
def webhook_logs(hook_id: str) -> WebhookLogsResult:
    """View execution logs for a webhook.

    Useful for debugging webhook delivery issues.

    Args:
        hook_id: The webhook ID (e.g., "hk_xxx")

    Returns:
        WebhookLogsResult with list of execution logs.
    """
    client = get_client()

    result = client.webhook_logs(hook_id)
    logs = result.get("logs", result.get("list", []))

    return WebhookLogsResult(logs=logs)


@mcp.tool
@wrap_api_error
def webhook_sample_payload(
    table_id: str,
    event: str = "records",
    operation: str = "insert",
    version: str = "v2",
) -> WebhookSamplePayloadResult:
    """Get a sample webhook payload for testing.

    Args:
        table_id: The table ID (e.g., "tbl_xxx")
        event: Event type - "records" (most common)
        operation: Operation type - "insert", "update", "delete"
        version: Payload version - "v1" or "v2" (default: "v2")

    Returns:
        WebhookSamplePayloadResult with sample payload structure.

    Example payload structure:
        {
            "event": "records",
            "operation": "insert",
            "row": {...},  # The affected record
            "table": {...},  # Table metadata
            ...
        }
    """
    client = get_client()

    result = client.webhook_sample_payload(table_id, event, operation, version)

    return WebhookSamplePayloadResult(payload=result)


@mcp.tool
@wrap_api_error
def webhook_filters_list(hook_id: str) -> WebhookFiltersListResult:
    """List filters for a webhook.

    Webhook filters determine when the webhook triggers based on field values.

    Args:
        hook_id: The webhook ID (e.g., "hk_xxx")

    Returns:
        WebhookFiltersListResult with list of filters.
    """
    client = get_client()

    result = client.webhook_filters_list(hook_id)
    filters = result.get("list", [])

    return WebhookFiltersListResult(filters=filters)


@mcp.tool
@wrap_api_error
def webhook_filter_create(
    hook_id: str,
    fk_column_id: str,
    comparison_op: str,
    value: Any = None,
) -> WebhookFilterResult:
    """Create a filter for a webhook.

    Filters control when the webhook fires based on field values.

    Args:
        hook_id: The webhook ID (e.g., "hk_xxx")
        fk_column_id: The column/field ID to filter on
        comparison_op: The comparison operator (eq, neq, like, etc.)
        value: The filter value

    Returns:
        WebhookFilterResult with created filter details.

    Example:
        # Only trigger webhook when Status is "Completed"
        webhook_filter_create("hk_xxx", "fld_status", "eq", "Completed")
    """
    client = get_client()

    body: dict[str, Any] = {
        "fk_column_id": fk_column_id,
        "comparison_op": comparison_op,
    }
    if value is not None:
        body["value"] = value

    result = client.webhook_filter_create(hook_id, body)

    return WebhookFilterResult(
        id=result.get("id", ""),
        fk_column_id=result.get("fk_column_id", fk_column_id),
        comparison_op=result.get("comparison_op", comparison_op),
        value=result.get("value", value),
    )
