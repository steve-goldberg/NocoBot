# NocoDB MCP Server Reference

You have access to the NocoDB MCP server for database operations on a self-hosted NocoDB instance.

## CRITICAL: Always Discover Schema First

**You MUST call `fields_list` or `table_get` BEFORE using `sort` or `where` parameters.**

The API returns 400 Bad Request if you use field names that don't exist. Field names cannot be guessed.

### Wrong (will fail with 400):
```
records_list(table_id="tbl_xxx", sort="-plays")  # Guessing "plays" exists
records_list(table_id="tbl_xxx", where="(status,eq,Active)")  # Guessing "status" exists
```

### Correct workflow:
```
1. fields_list(table_id="tbl_xxx")
   # Returns actual fields: Title, Views, CreatedAt, Status, ...

2. records_list(table_id="tbl_xxx", sort="-Views", where="(Status,eq,Active)")
   # Use exact field names from step 1
```

### Field names are:
- **Case-sensitive** - "Status" ≠ "status"
- **Must match exactly** - Use the title returned by fields_list
- **Never guess** - Always discover first

---

## Required Workflow

```
1. tables_list              → Get table IDs
2. fields_list(table_id)    → REQUIRED before sort/where - get exact field names
3. records_list(...)        → Query using actual field names from step 2
```

---

## Quick Reference

## Tool Categories

### Records (Data API)
| Tool | Description |
|------|-------------|
| `records_list` | List records with filtering/pagination |
| `records_list_all` | Fetch all records (handles pagination) |
| `record_get` | Get single record by ID |
| `records_create` | Create one or more records |
| `records_update` | Update records (requires id in each record) |
| `records_delete` | Delete records (**confirm=True required**) |
| `records_count` | Count records matching filter |

### Tables & Fields (Meta API)
| Tool | Description |
|------|-------------|
| `tables_list` | List all tables |
| `table_get` | Get table with fields |
| `table_create` | Create table with optional fields |
| `table_update` | Update table title/icon/meta |
| `table_delete` | Delete table (**confirm=True required**) |
| `fields_list` | List fields in table |
| `field_get` | Get field details |
| `field_create` | Create new field |
| `field_update` | Update field title/options |
| `field_update_options` | Update colOptions (v2 API for colors) |
| `field_delete` | Delete field (**confirm=True required**) |

### Links (Relationships)
| Tool | Description |
|------|-------------|
| `linked_records_list` | List records linked via Links field |
| `linked_records_link` | Link records together |
| `linked_records_unlink` | Unlink records (**confirm=True required**) |

### Views
| Tool | Description |
|------|-------------|
| `views_list` | List views for a table |
| `view_update` | Update view title/icon |
| `view_delete` | Delete view (**confirm=True required**) |

### View Filters & Sorts
| Tool | Description |
|------|-------------|
| `view_filters_list` | List view filters |
| `view_filter_create` | Create filter |
| `view_filter_update` | Update filter |
| `view_filter_delete` | Delete filter (**confirm=True required**) |
| `view_sorts_list` | List view sorts |
| `view_sort_create` | Create sort |
| `view_sort_update` | Update sort |
| `view_sort_delete` | Delete sort (**confirm=True required**) |

### View Columns & Sharing
| Tool | Description |
|------|-------------|
| `view_columns_list` | List column visibility |
| `view_column_update` | Update column show/order |
| `view_columns_hide_all` | Hide all columns |
| `view_columns_show_all` | Show all columns |
| `shared_views_list` | List public share links |
| `shared_view_create` | Create public link |
| `shared_view_update` | Update share settings |
| `shared_view_delete` | Remove public link (**confirm=True required**) |

### Webhooks
| Tool | Description |
|------|-------------|
| `webhooks_list` | List webhooks for table |
| `webhook_delete` | Delete webhook (**confirm=True required**) |
| `webhook_logs` | View webhook execution logs |
| `webhook_sample_payload` | Get sample payload |
| `webhook_filters_list` | List webhook filters |
| `webhook_filter_create` | Create webhook filter |

### Other
| Tool | Description |
|------|-------------|
| `members_list` | List base members |
| `member_add` | Add member to base |
| `member_update` | Update member role |
| `member_remove` | Remove member (**confirm=True required**) |
| `attachment_upload` | Upload file to record field |
| `storage_upload` | Upload file to general storage |
| `export_csv` | Export view as CSV |

---

## Field Types

| Type | Description | Options Example |
|------|-------------|-----------------|
| `SingleLineText` | Short text | - |
| `LongText` | Multi-line text | - |
| `Number` | Integer | - |
| `Decimal` | Float | `{"precision": 2}` |
| `Currency` | Money | `{"locale": "en-US", "code": "USD"}` |
| `Percent` | Percentage | - |
| `Email` | Email address | - |
| `URL` | Web link | - |
| `PhoneNumber` | Phone | - |
| `Date` | Date only | `{"date_format": "YYYY-MM-DD"}` |
| `DateTime` | Date + time | - |
| `Time` | Time only | - |
| `Duration` | Time span | - |
| `Checkbox` | Boolean | - |
| `SingleSelect` | Dropdown | `{"options": {"choices": [{"title": "A", "color": "#00FF00"}]}}` |
| `MultiSelect` | Multi-dropdown | Same as SingleSelect |
| `Rating` | Star rating | `{"max": 5}` |
| `Attachment` | File upload | - |
| `Links` | Relationship | `{"relation_type": "hm", "related_table_id": "tbl_xxx"}` |
| `Lookup` | Related field | - |
| `Rollup` | Aggregation | - |
| `Formula` | Calculated | `{"formula": "..."}` |

**Note:** For SingleSelect/MultiSelect colors, use HEX codes (`#00FF00`), not color names.

---

## Filter Syntax

Use in `where` parameter for records_list:

| Operator | Syntax | Example |
|----------|--------|---------|
| Equal | `eq` | `(Status,eq,Active)` |
| Not equal | `neq` | `(Status,neq,Deleted)` |
| Greater than | `gt` | `(Age,gt,18)` |
| Greater or equal | `gte` | `(Age,gte,21)` |
| Less than | `lt` | `(Price,lt,100)` |
| Less or equal | `lte` | `(Price,lte,50)` |
| Like | `like` | `(Name,like,%john%)` |
| Is null/notnull | `is` | `(Email,is,notnull)` |
| In list | `in` | `(Status,in,Active,Pending)` |
| Between | `btw` | `(Age,btw,18,65)` |
| And | `~and` | `(A,eq,1)~and(B,eq,2)` |
| Or | `~or` | `(A,eq,1)~or(A,eq,2)` |

---

## Common Workflows

### Create a Table with Records

```python
# 1. Create table with fields
table_create(
    title="Contacts",
    fields=[
        {"title": "Name", "type": "SingleLineText"},
        {"title": "Email", "type": "Email"},
        {"title": "Status", "type": "SingleSelect", "dtxp": "Active,Inactive"}
    ]
)

# 2. Create records
records_create(
    table_id="tbl_xxx",
    records=[
        {"Name": "Alice", "Email": "alice@example.com", "Status": "Active"},
        {"Name": "Bob", "Email": "bob@example.com", "Status": "Inactive"}
    ]
)
```

### Query with Filters

```python
# Active users
records_list(table_id="tbl_xxx", where="(Status,eq,Active)")

# Search by name
records_list(table_id="tbl_xxx", where="(Name,like,%john%)")

# Multiple conditions
records_list(table_id="tbl_xxx", where="(Status,eq,Active)~and(Age,gt,21)")
```

### Create Related Tables

```python
# 1. Create parent table (Projects)
table_create(title="Projects", fields=[{"title": "Name", "type": "SingleLineText"}])

# 2. Create child table (Tasks)
table_create(title="Tasks", fields=[{"title": "Title", "type": "SingleLineText"}])

# 3. Add Links field to child table
field_create(
    table_id="tbl_tasks",
    title="Project",
    field_type="Links",
    options={"relation_type": "hm", "related_table_id": "tbl_projects"}
)

# 4. Link a task to a project
linked_records_link(
    table_id="tbl_tasks",
    link_field_id="fld_project",
    record_id="1",
    target_ids=["5"]  # Project ID
)
```

### Update Record

```python
records_update(
    table_id="tbl_xxx",
    records=[
        {"id": 1, "Status": "Completed"},
        {"id": 2, "Status": "Completed"}
    ]
)
```

---

## Limitations (Self-Hosted Community Edition)

| Feature | Status | Notes |
|---------|--------|-------|
| Bases | list only | Cannot create via API |
| Tables | full CRUD | ✅ |
| Fields | full CRUD | ✅ |
| Records | full CRUD | ✅ |
| Links | full CRUD | ✅ |
| Views | list, update, delete | Cannot create views via API |
| View Filters/Sorts | full CRUD | ✅ |
| View Columns | full CRUD | ✅ |
| Shared Views | full CRUD | ✅ |
| Webhooks | list, delete | Cannot create/update via API |
| Webhook Logs | read | ✅ |
| Webhook Filters | list, create | ✅ |
| Export CSV | export | ✅ |
| Storage | upload | ✅ |
| Attachments | upload | ✅ |
| Members | full CRUD | ✅ |

**Use NocoDB web UI to create:** bases, views, webhooks.

---

## Destructive Operations

All destructive operations require `confirm=True`:
- `records_delete`
- `table_delete`
- `field_delete`
- `view_delete`
- `view_filter_delete`
- `view_sort_delete`
- `shared_view_delete`
- `webhook_delete`
- `member_remove`
- `linked_records_unlink`

Example:
```python
records_delete(table_id="tbl_xxx", record_ids=["1", "2"], confirm=True)
```

---

## Tips

1. **ALWAYS discover schema first** - Call `fields_list` before using `sort` or `where` parameters
2. **Field names are case-sensitive** - Use exact names from `fields_list` output
3. **Use field IDs for some tools** - Links, field operations require `fld_xxx` format IDs
4. **Batch operations** - `records_create` and `records_update` accept lists
5. **Pagination** - Use `page` and `page_size` for large datasets, or `records_list_all` for everything
6. **Filter syntax** - Remember the parentheses: `(FieldName,op,value)` with exact field name
