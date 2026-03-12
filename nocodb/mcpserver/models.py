"""Response models for NocoDB MCP server.

These dataclasses provide structured output schemas for MCP tools,
enabling clients to receive typed, predictable responses.
"""

from dataclasses import dataclass, field
from typing import Any


# =============================================================================
# Records
# =============================================================================

@dataclass
class RecordsListResult:
    """Result from listing records."""
    records: list[dict[str, Any]]
    page: int = 1
    page_size: int = 25
    has_next: bool = False


@dataclass
class RecordResult:
    """Result from getting a single record."""
    id: int | str
    fields: dict[str, Any]


@dataclass
class RecordsCountResult:
    """Result from counting records."""
    count: int


@dataclass
class RecordsMutationResult:
    """Result from creating/updating/deleting records."""
    success: bool
    records: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""


# =============================================================================
# Tables
# =============================================================================

@dataclass
class TablesListResult:
    """Result from listing tables."""
    tables: list[dict[str, Any]]


@dataclass
class TableResult:
    """Result from getting/creating/updating a table."""
    id: str
    title: str
    fields: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] | None = None


@dataclass
class TableDeleteResult:
    """Result from deleting a table."""
    success: bool
    message: str = ""


# =============================================================================
# Fields
# =============================================================================

@dataclass
class FieldsListResult:
    """Result from listing fields."""
    fields: list[dict[str, Any]]


@dataclass
class FieldResult:
    """Result from getting/creating/updating a field."""
    id: str
    title: str
    type: str
    options: dict[str, Any] | None = None


@dataclass
class FieldDeleteResult:
    """Result from deleting a field."""
    success: bool
    message: str = ""


# =============================================================================
# Bases
# =============================================================================

@dataclass
class BasesListResult:
    """Result from listing bases."""
    bases: list[dict[str, Any]]


@dataclass
class BaseInfoResult:
    """Result from getting base info."""
    id: str
    title: str
    tables: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] | None = None


# =============================================================================
# Links
# =============================================================================

@dataclass
class LinkedRecordsResult:
    """Result from listing/linking/unlinking records."""
    records: list[dict[str, Any]]
    has_next: bool = False


# =============================================================================
# Views
# =============================================================================

@dataclass
class ViewsListResult:
    """Result from listing views."""
    views: list[dict[str, Any]]


@dataclass
class ViewResult:
    """Result from updating a view."""
    id: str
    title: str
    type: int
    meta: dict[str, Any] | None = None


@dataclass
class ViewDeleteResult:
    """Result from deleting a view."""
    success: bool
    message: str = ""


# =============================================================================
# View Filters
# =============================================================================

@dataclass
class ViewFiltersListResult:
    """Result from listing view filters."""
    filters: list[dict[str, Any]]


@dataclass
class ViewFilterResult:
    """Result from getting/creating/updating a filter."""
    id: str
    fk_column_id: str
    comparison_op: str
    value: Any = None


@dataclass
class ViewFilterDeleteResult:
    """Result from deleting a filter."""
    success: bool
    message: str = ""


# =============================================================================
# View Sorts
# =============================================================================

@dataclass
class ViewSortsListResult:
    """Result from listing view sorts."""
    sorts: list[dict[str, Any]]


@dataclass
class ViewSortResult:
    """Result from getting/creating/updating a sort."""
    id: str
    fk_column_id: str
    direction: str = "asc"


@dataclass
class ViewSortDeleteResult:
    """Result from deleting a sort."""
    success: bool
    message: str = ""


# =============================================================================
# View Columns
# =============================================================================

@dataclass
class ViewColumnsListResult:
    """Result from listing view columns."""
    columns: list[dict[str, Any]]


@dataclass
class ViewColumnResult:
    """Result from updating a view column."""
    id: str
    fk_column_id: str
    show: bool = True
    order: int = 0


# =============================================================================
# Shared Views
# =============================================================================

@dataclass
class SharedViewsListResult:
    """Result from listing shared views."""
    shared_views: list[dict[str, Any]]


@dataclass
class SharedViewResult:
    """Result from creating/updating a shared view."""
    uuid: str
    url: str | None = None


@dataclass
class SharedViewDeleteResult:
    """Result from deleting a shared view."""
    success: bool
    message: str = ""


# =============================================================================
# Webhooks
# =============================================================================

@dataclass
class WebhooksListResult:
    """Result from listing webhooks."""
    webhooks: list[dict[str, Any]]


@dataclass
class WebhookDeleteResult:
    """Result from deleting a webhook."""
    success: bool
    message: str = ""


@dataclass
class WebhookLogsResult:
    """Result from getting webhook logs."""
    logs: list[dict[str, Any]]


@dataclass
class WebhookSamplePayloadResult:
    """Result from getting webhook sample payload."""
    payload: dict[str, Any]


@dataclass
class WebhookFiltersListResult:
    """Result from listing webhook filters."""
    filters: list[dict[str, Any]]


@dataclass
class WebhookFilterResult:
    """Result from creating a webhook filter."""
    id: str
    fk_column_id: str
    comparison_op: str
    value: Any = None


# =============================================================================
# Members
# =============================================================================

@dataclass
class MembersListResult:
    """Result from listing base members."""
    members: list[dict[str, Any]]


@dataclass
class MemberResult:
    """Result from adding/updating a member."""
    id: str
    email: str
    roles: str


@dataclass
class MemberDeleteResult:
    """Result from removing a member."""
    success: bool
    message: str = ""


# =============================================================================
# Attachments & Storage
# =============================================================================

@dataclass
class AttachmentUploadResult:
    """Result from uploading an attachment."""
    url: str
    title: str
    mimetype: str
    size: int | None = None


@dataclass
class StorageUploadResult:
    """Result from uploading to storage."""
    url: str
    title: str
    mimetype: str


# =============================================================================
# Export
# =============================================================================

@dataclass
class ExportResult:
    """Result from exporting a view."""
    csv_content: str
    row_count: int | None = None


# =============================================================================
# Schema Export
# =============================================================================

@dataclass
class TableSchemaResult:
    """Result from exporting a table schema."""
    title: str
    fields: list[dict[str, Any]]


@dataclass
class BaseSchemaResult:
    """Result from exporting a base schema."""
    title: str
    tables: list[dict[str, Any]]
    description: str | None = None
