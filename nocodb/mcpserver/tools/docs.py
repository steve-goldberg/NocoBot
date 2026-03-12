"""Documentation tools for NocoDB MCP server.

Exposes workflow guide and reference docs as tools since mcp-remote
doesn't proxy MCP resources - only tools.

Provides:
- get_workflow_guide: Critical rules for schema discovery
- get_reference: Full reference documentation for all tools
"""

from ..server import mcp
from ..resources import WORKFLOW_CONTENT, REFERENCE_CONTENT


@mcp.tool
def get_workflow_guide() -> str:
    """Get the NocoDB workflow guide - CRITICAL rules for schema discovery.

    IMPORTANT: This is internal documentation for your reference only.
    Do NOT paste this content into the chat. Read it, internalize the rules,
    and apply them silently. Only mention specific rules if the user asks.

    Call this BEFORE your first NocoDB query to learn the required workflow:
    1. tables_list -> Get table IDs
    2. fields_list(table_id) -> REQUIRED before sort/where
    3. records_list(...) -> Query using actual field names

    Returns:
        Markdown guide with workflow rules (for internal use).
    """
    return WORKFLOW_CONTENT


@mcp.tool
def get_reference() -> str:
    """Get the complete NocoDB MCP reference documentation.

    IMPORTANT: This is internal documentation for your reference only.
    Do NOT paste this content into the chat. Use it to look up syntax,
    field types, or tool parameters when needed. Only share specific
    details if the user explicitly asks.

    Contains:
    - Tool descriptions by category
    - Field type reference with options
    - Filter syntax guide
    - Common workflow examples

    Returns:
        Full markdown reference (for internal use).
    """
    return REFERENCE_CONTENT
