# NocoDB API v2/v3 Reference

This guide documents the hybrid v2/v3 API approach used by this client for self-hosted NocoDB community edition.

## Overview

Self-hosted NocoDB requires a mix of v2 and v3 APIs:

- **v3 Data API** - All record operations (CRUD, links, attachments)
- **v3 Meta API** - Tables, fields, single base operations, base members
- **v2 Meta API** - List bases, views, view filters/sorts, list/delete webhooks

Some v3 Meta endpoints are Enterprise-only and return 404 on self-hosted.

## API Version Reference

| Feature | API | Endpoint | Notes |
|---------|-----|----------|-------|
| Records CRUD | v3 | `/api/v3/data/{baseId}/{tableId}/records` | Full support |
| Linked Records | v3 | `/api/v3/data/{baseId}/{tableId}/links/...` | Full support |
| Attachments | v3 | `/api/v3/data/.../upload` | Full support |
| List Bases | v2 | `/api/v2/meta/bases` | v3 requires Enterprise |
| Get/Update/Delete Base | v3 | `/api/v3/meta/bases/{baseId}` | Works in community |
| Base Members | v3 | `/api/v3/meta/bases/{baseId}/members` | Full support |
| Tables CRUD | v3 | `/api/v3/meta/bases/{baseId}/tables` | Full support |
| Fields CRUD | v3 | `/api/v3/meta/bases/{baseId}/tables/{tableId}/fields` | Full support |
| Views (list/update/delete) | v2 | `/api/v2/meta/tables/{tableId}/views` | create/get broken |
| View Filters | v2 | `/api/v2/meta/views/{viewId}/filters` | Full CRUD |
| View Sorts | v2 | `/api/v2/meta/views/{viewId}/sorts` | Full CRUD |
| Webhooks (list/delete) | v2 | `/api/v2/meta/tables/{tableId}/hooks` | create/get/update/test broken |

## v3 Data API

### Response Format

v3 records use a nested structure with `id` and `fields`:

```json
{
  "id": 1,
  "fields": {
    "Name": "John Doe",
    "Email": "john@example.com",
    "Status": "Active"
  }
}
```

### List Response

```json
{
  "records": [
    {"id": 1, "fields": {"Name": "John"}},
    {"id": 2, "fields": {"Name": "Jane"}}
  ],
  "next": "http://localhost:8080/api/v3/data/.../records?page=2"
}
```

### Batch Operations

v3 methods accept arrays for batch operations:

```python
# Create multiple records
new_records = client.records_create_v3(base_id, table_id, [
    {"fields": {"Name": "John"}},
    {"fields": {"Name": "Jane"}}
])

# Update multiple records (ID in payload)
client.records_update_v3(base_id, table_id, [
    {"id": 1, "fields": {"Status": "Done"}},
    {"id": 2, "fields": {"Status": "Done"}}
])

# Delete multiple records
client.records_delete_v3(base_id, table_id, [1, 2, 3])
```

### Linked Records

```python
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

## v2 Meta API

### Response Format

v2 endpoints return data in a `list` array:

```json
{
  "list": [
    {"id": "base_abc", "title": "My Base"},
    {"id": "base_def", "title": "Other Base"}
  ]
}
```

### Bases

```python
# List all bases (v2 API)
bases = client.bases_list_v3()
# Response: {"list": [{"id": "base_abc", "title": "My Base"}]}

# Get single base (v3 API)
base = client.base_read_v3(base_id)

# Update base (v3 API)
client.base_update_v3(base_id, {"title": "New Name"})

# Delete base (v3 API)
client.base_delete_v3(base_id)
```

### Views

```python
# List views (v2 API)
views = client.views_list(table_id)

# Update view (v2 API)
client.view_update(view_id, {"title": "New View Name"})

# Delete view (v2 API)
client.view_delete(view_id)

# Note: view_create and view_get are broken in self-hosted
```

### View Filters

```python
# List filters
filters = client.view_filters_list(view_id)

# Create filter
client.view_filter_create(view_id, {
    "fk_column_id": "col_abc",
    "comparison_op": "eq",
    "value": "Active"
})

# Update filter
client.view_filter_update(filter_id, {"value": "Inactive"})

# Delete filter
client.view_filter_delete(filter_id)
```

### View Sorts

```python
# List sorts
sorts = client.view_sorts_list(view_id)

# Create sort
client.view_sort_create(view_id, {
    "fk_column_id": "col_abc",
    "direction": "asc"
})

# Update sort
client.view_sort_update(sort_id, {"direction": "desc"})

# Delete sort
client.view_sort_delete(sort_id)
```

### Webhooks

```python
# List webhooks (v2 API)
webhooks = client.webhooks_list(table_id)

# Delete webhook (v2 API)
client.webhook_delete(hook_id)

# Note: webhook_create, webhook_get, webhook_update, webhook_test
# are broken in self-hosted NocoDB
```

## Filter Syntax

Filters use the format `(field,operator,value)` with `~and`/`~or` combinators:

```python
from nocodb.filters import EqFilter, LikeFilter, And, Or, IsFilter, InFilter, BetweenFilter

# Simple filter
EqFilter("Status", "Active").get_where()
# Output: (Status,eq,Active)

# Combined with AND
And(
    EqFilter("Status", "Active"),
    LikeFilter("Name", "%test%")
).get_where()
# Output: (Status,eq,Active)~and(Name,like,%test%)

# Combined with OR
Or(
    EqFilter("Status", "Active"),
    EqFilter("Status", "Pending")
).get_where()
# Output: (Status,eq,Active)~or(Status,eq,Pending)

# Null/empty checks
IsFilter("Status", "notnull").get_where()   # (Status,is,notnull)
IsFilter("Notes", "empty").get_where()       # (Notes,is,empty)

# Match list of values
InFilter("Tags", ["urgent", "important"]).get_where()
# Output: (Tags,in,urgent,important)

# Range matching
BetweenFilter("Age", 18, 65).get_where()
# Output: (Age,btw,18,65)
```

### Available Operators

| Filter Class | Operator | Example |
|-------------|----------|---------|
| `EqFilter` | `eq` | `(Status,eq,Active)` |
| `NotEqualFilter` | `neq` | `(Status,neq,Deleted)` |
| `GreaterThanFilter` | `gt` | `(Age,gt,18)` |
| `GreaterOrEqualFilter` | `gte` | `(Age,gte,18)` |
| `LessThanFilter` | `lt` | `(Age,lt,65)` |
| `LessOrEqualFilter` | `lte` | `(Age,lte,65)` |
| `LikeFilter` | `like` | `(Name,like,%test%)` |
| `NotLikeFilter` | `nlike` | `(Name,nlike,%test%)` |
| `IsFilter` | `is` | `(Status,is,null)` |
| `InFilter` | `in` | `(Tags,in,a,b,c)` |
| `BetweenFilter` | `btw` | `(Age,btw,18,65)` |

### IsFilter Values

- `null` / `notnull` - Check for null values
- `true` / `false` - Check boolean values
- `empty` / `notempty` - Check for empty strings

## Enterprise-Only Features

These features require NocoDB Enterprise and are NOT available in self-hosted:

- **Workspaces** - Multi-tenant hierarchy above bases
- **Teams** - Team management
- **Workspace members** - Member management within workspaces
- **v3 Views API** - Use v2 `views_list()` instead
- **v3 Bases list** - Use v2 `bases_list_v3()` instead

## Broken in Self-Hosted

These v2 operations return 404 or errors and have been removed from this client:

- `webhook_create()` - Returns 404
- `webhook_get()` - Returns 404
- `webhook_update()` - Returns 404
- `webhook_test()` - Returns 404
- `view_create()` - Returns 404
- `view_get()` - Returns 404

Use the NocoDB web UI to create webhooks and views, then manage them via API.
