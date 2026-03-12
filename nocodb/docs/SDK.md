# Python SDK Documentation

Complete Python client for NocoDB API (self-hosted community edition).

## Installation

```bash
# Using uv (recommended)
uv pip install git+https://github.com/steve-goldberg/nocodb-py.git

# Using pip
pip install git+https://github.com/steve-goldberg/nocodb-py.git

# From source
git clone https://github.com/steve-goldberg/nocodb-py.git
cd nocodb-py
pip install -e .
```

## Client Setup

```python
from nocodb import NocoDBBase, APIToken
from nocodb.infra.requests_client import NocoDBRequestsClient

# Create client with API token
client = NocoDBRequestsClient(
    APIToken("YOUR-API-TOKEN"),
    "http://localhost:8080"  # Your NocoDB instance URL
)

# Define base and table IDs (from NocoDB URL or API)
base_id = "pgfqcp0ocloo1j3"    # e.g., from URL: /dashboard/#/nc/pgfqcp0ocloo1j3
table_id = "mq31p5ngbwj5o7u"   # e.g., from table settings
```

## v3 Data API

### Records CRUD

```python
# List records
result = client.records_list_v3(base_id, table_id)
# Response: {"records": [{"id": 1, "fields": {"Name": "...", "Status": "..."}}], "next": "..."}

# Access records from response
for record in result["records"]:
    print(f"ID: {record['id']}, Name: {record['fields']['Name']}")

# Get single record
record = client.record_get_v3(base_id, table_id, 1)
# Response: {"id": 1, "fields": {"Name": "John", "Status": "Active"}}

# Create records (batch)
new_records = client.records_create_v3(base_id, table_id, [
    {"fields": {"Name": "Record 1", "Status": "Active"}},
    {"fields": {"Name": "Record 2", "Status": "Draft"}}
])
# Response: [{"id": 1, "fields": {...}}, {"id": 2, "fields": {...}}]

# Update records (batch)
updated = client.records_update_v3(base_id, table_id, [
    {"id": 1, "fields": {"Status": "Complete"}},
    {"id": 2, "fields": {"Status": "Active"}}
])

# Delete records (batch)
deleted = client.records_delete_v3(base_id, table_id, [1, 2])
# Response: [{"id": 1}, {"id": 2}]

# Count records
count_result = client.records_count_v3(base_id, table_id)
# Response: {"count": 42}
```

### Query Parameters

```python
# Pagination
result = client.records_list_v3(base_id, table_id, params={
    "page": 1,
    "pageSize": 25
})

# Select specific fields
result = client.records_list_v3(base_id, table_id, params={
    "fields": "Name,Status,CreatedAt"
})

# Sort records (prefix with - for descending)
result = client.records_list_v3(base_id, table_id, params={
    "sort": "-CreatedAt,Name"
})

# Filter with view
result = client.records_list_v3(base_id, table_id, params={
    "viewId": "vw_abc123"
})
```

### Linked Records

```python
link_field_id = "lk_abc123"
record_id = 1

# List linked records
linked = client.linked_records_list_v3(base_id, table_id, link_field_id, record_id)
# Response: {"list": [{"id": 22, "fields": {...}}], "next": "url"}

# Link records
client.linked_records_link_v3(base_id, table_id, link_field_id, record_id,
    link_records=[{"id": 22}, {"id": 43}])

# Unlink records
client.linked_records_unlink_v3(base_id, table_id, link_field_id, record_id,
    unlink_records=[{"id": 22}])
```

### Attachments

```python
# Upload attachment to a record's attachment field
client.attachment_upload_v3(
    base_id, table_id, record_id, field_id,
    filename="document.pdf",
    content_type="application/pdf",
    file_content=base64_encoded_content
)
```

## v3 Meta API

### Tables

```python
# List tables in a base
tables = client.tables_list_v3(base_id)
# Response: {"list": [{"id": "tbl_abc", "title": "My Table"}]}

# Get table schema
table_meta = client.table_get_v3(base_id, table_id)

# Create table
client.table_create_v3(base_id, {"title": "New Table"})

# Update table
client.table_update_v3(base_id, table_id, {"title": "Renamed Table"})

# Delete table
client.table_delete_v3(base_id, table_id)
```

### Fields

```python
# List fields
fields = client.fields_list_v3(base_id, table_id)

# Get field details
field = client.field_read_v3(base_id, field_id)

# Create field
client.field_create_v3(base_id, table_id, {"title": "New Field", "type": "SingleLineText"})

# Update field
client.field_update_v3(base_id, field_id, {"title": "Renamed Field"})

# Delete field
client.field_delete_v3(base_id, field_id)
```

### Base Members

```python
# List members
members = client.base_members_list(base_id)

# Add member
client.base_member_add(base_id, {"email": "user@example.com", "role": "editor"})

# Update member role
client.base_member_update(base_id, user_id, {"role": "viewer"})

# Remove member
client.base_member_remove(base_id, user_id)
```

## v2 Meta API

### Bases

```python
# List all bases (v2 API - required for self-hosted)
bases = client.bases_list_v3()
# Response: {"list": [{"id": "base_abc", "title": "My Base"}]}
```

### Views

```python
# List views for a table
views = client.views_list(table_id)

# Update view
client.view_update(view_id, {"title": "Renamed View"})

# Delete view
client.view_delete(view_id)
```

### View Filters

```python
# List filters
filters = client.view_filters_list(view_id)

# Create filter
client.view_filter_create(view_id, {
    "fk_column_id": "col_id",
    "comparison_op": "eq",
    "value": "test"
})

# Update filter
client.view_filter_update(filter_id, {"value": "new_value"})

# Delete filter
client.view_filter_delete(filter_id)
```

### View Sorts

```python
# List sorts
sorts = client.view_sorts_list(view_id)

# Create sort
client.view_sort_create(view_id, {"fk_column_id": "col_id", "direction": "asc"})

# Update sort
client.view_sort_update(sort_id, {"direction": "desc"})

# Delete sort
client.view_sort_delete(sort_id)
```

### View Columns

```python
# List columns
columns = client.view_columns_list(view_id)

# Update column visibility/order
client.view_column_update(view_id, column_id, {"show": True, "order": 1})

# Hide all columns
client.view_columns_hide_all(view_id)

# Show all columns
client.view_columns_show_all(view_id)
```

### Shared Views

```python
# Create shared view (public link)
shared = client.shared_view_create(view_id, {"password": "optional-password"})

# List shared views for table
shared_views = client.shared_views_list(table_id)

# Update shared view
client.shared_view_update(view_id, {"password": "new-password"})

# Delete shared view
client.shared_view_delete(view_id)
```

### Webhooks

```python
# List webhooks (list/delete only in self-hosted)
webhooks = client.webhooks_list(table_id)

# Delete webhook
client.webhook_delete(hook_id)

# Get webhook logs
logs = client.webhook_logs(hook_id)

# Get sample payload
sample = client.webhook_sample_payload(table_id, "records", "insert", "v2")

# Webhook filters
filters = client.webhook_filters_list(hook_id)
client.webhook_filter_create(hook_id, {
    "fk_column_id": "col_id",
    "comparison_op": "eq",
    "value": "test"
})
```

### Export & Storage

```python
# Export view to CSV
csv_content = client.export_view(view_id)

# Upload file to storage
result = client.storage_upload(file_path, content_type="application/pdf")
```

## Response Format

The v3 API returns records in a nested format:

```python
# v3 record structure
{
    "id": 1,
    "fields": {
        "Name": "John Doe",
        "Email": "john@example.com",
        "Status": "Active",
        "CreatedAt": "2024-01-15T10:30:00.000Z"
    }
}

# v3 list response
{
    "records": [
        {"id": 1, "fields": {"Name": "John", ...}},
        {"id": 2, "fields": {"Name": "Jane", ...}}
    ],
    "next": "http://localhost:8080/api/v3/data/.../records?page=2"
}
```

## API Version Reference

| Feature | API | Endpoint Pattern |
|---------|-----|------------------|
| Records CRUD | v3 | `/api/v3/data/{baseId}/{tableId}/records` |
| Linked Records | v3 | `/api/v3/data/{baseId}/{tableId}/links/{linkFieldId}/{recordId}` |
| Attachments | v3 | `/api/v3/data/.../records/{recordId}/fields/{fieldId}/upload` |
| List Bases | v2 | `/api/v2/meta/bases` |
| Base CRUD | v3 | `/api/v3/meta/bases/{baseId}` |
| Base Members | v3 | `/api/v3/meta/bases/{baseId}/members` |
| Tables CRUD | v3 | `/api/v3/meta/bases/{baseId}/tables` |
| Fields CRUD | v3 | `/api/v3/meta/bases/{baseId}/tables/{tableId}/fields` |
| Views | v2 | `/api/v2/meta/tables/{tableId}/views` |
| View Filters/Sorts | v2 | `/api/v2/meta/views/{viewId}/filters` |
| Export CSV | v2 | `/api/v2/export/{viewId}/csv` |
| Storage Upload | v2 | `/api/v2/storage/upload` |
| Webhooks | v2 | `/api/v2/meta/tables/{tableId}/hooks` |

## Not Supported (Enterprise Only)

These features require NocoDB Enterprise:

- Workspaces (multi-tenant hierarchy)
- Teams management
- Workspace members
- v3 Views API
- v3 Bases list endpoint
- API Token Management via API
- Button Actions trigger API

## Related Documentation

- [Filters](FILTERS.md) - Query filter system
- [CLI](CLI.md) - Command-line interface
- [MCP Server](MCP.md) - AI assistant integration
- [Migration Guide](MIGRATION.md) - v1 to v3 migration
