"""NocoDB MCP tools.

Each module registers tools with the FastMCP server when imported.
Import order doesn't matter - all tools are registered during server startup.
"""

from . import (
    records,
    bases,
    tables,
    fields,
    links,
    views,
    view_filters,
    view_sorts,
    view_columns,
    shared_views,
    webhooks,
    members,
    attachments,
    storage,
    export,
    schema,
    docs,
)

__all__ = [
    "records",
    "bases",
    "tables",
    "fields",
    "links",
    "views",
    "view_filters",
    "view_sorts",
    "view_columns",
    "shared_views",
    "webhooks",
    "members",
    "attachments",
    "storage",
    "export",
    "schema",
    "docs",
]
