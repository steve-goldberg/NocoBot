---
name: "nocodb-cli"
description: "CLI for the NocoDB MCP server. Call tools, list resources, and get prompts."
---

# NocoDB CLI

## Tool Commands

### records_list

List records from a table with optional filtering and pagination.

```bash
nocodb call-tool records_list --table-id <value> --fields <value> --sort <value> --where <value> --page <value> --page-size <value> --view-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--fields` | string | no | Comma-separated field names to include (e.g., "Name,Email,Status") (JSON string) |
| `--sort` | string | no | Sort field(s), prefix with - for descending (e.g., "-CreatedAt" or "Name,-Age") (JSON string) |
| `--where` | string | no | Filter condition using NocoDB syntax (e.g., "(Status,eq,Active)") (JSON string) |
| `--page` | integer | no | Page number (1-indexed, default: 1) |
| `--page-size` | integer | no | Records per page (default: 25, max: 1000) |
| `--view-id` | string | no | Optional view ID to filter by (JSON string) |

### records_list_all

Fetch all records from a table, automatically handling pagination.

Use with caution on large tables. Consider using records_list with
pagination for better control.

```bash
nocodb call-tool records_list_all --table-id <value> --where <value> --page-size <value> --max-pages <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--where` | string | no | Optional filter condition (JSON string) |
| `--page-size` | integer | no | Records per page (default: 100) |
| `--max-pages` | string | no | Maximum pages to fetch (None = unlimited) (JSON string) |

### record_get

Get a single record by ID.

```bash
nocodb call-tool record_get --table-id <value> --record-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--record-id` | string | yes | The record ID (e.g., "1" or "rec_xxx") |

### records_create

Create one or more records in a table.

```bash
nocodb call-tool records_create --table-id <value> --records <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--records` | array[object] | yes | List of record data dicts. Each dict should contain field values. Example: [{"Name": "John", "Email": "john@example.com"}] For batch: [{"Name": "A"}, {"Name": "B"}, {"Name": "C"}] (JSON string) |

### records_update

Update one or more records in a table.

```bash
nocodb call-tool records_update --table-id <value> --records <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--records` | array[object] | yes | List of record updates. Each dict must have "id" and field values. Example: [{"id": 1, "Status": "Done"}] For batch: [{"id": 1, "Status": "A"}, {"id": 2, "Status": "B"}] (JSON string) |

### records_delete

Delete one or more records from a table.

DESTRUCTIVE: This operation cannot be undone. Set confirm=True to proceed.

```bash
nocodb call-tool records_delete --table-id <value> --record-ids <value> --confirm
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--record-ids` | array[string] | yes | List of record IDs to delete (e.g., ["1", "2", "3"]) |
| `--confirm` | boolean | no | Must be True to proceed with deletion |

### records_count

Count records in a table, optionally filtered.

```bash
nocodb call-tool records_count --table-id <value> --where <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--where` | string | no | Optional filter condition (e.g., "(Status,eq,Active)") (JSON string) |

### bases_list

List all bases available to the current user.

Use this to discover base IDs for configuration.

Returns:
    BasesListResult with list of bases including id and title.

Note: The MCP server requires NOCODB_BASE_ID to be set.
This tool helps you find available base IDs if you need
to configure a different base.

```bash
nocodb call-tool bases_list
```

### base_info

Get detailed information about the currently configured base.

Returns the base metadata including title and list of tables.

Returns:
    BaseInfoResult with base id, title, tables, and metadata.

```bash
nocodb call-tool base_info
```

### tables_list

List all tables in the current base.

Returns:
    TablesListResult with list of tables including id, title, and type.

```bash
nocodb call-tool tables_list
```

### table_get

Get detailed information about a table including its fields.

```bash
nocodb call-tool table_get --table-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |

### table_create

Create a new table in the current base.

```bash
nocodb call-tool table_create --title <value> --fields <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--title` | string | yes | The table title (e.g., "Users", "Tasks") |
| `--fields` | string | no | Optional list of field definitions to create with the table. Each field should have "title" and "type" keys. Example: [{"title": "Name", "type": "SingleLineText"}, {"title": "Email", "type": "Email"}] (JSON string) |

### table_update

Update a table's metadata.

```bash
nocodb call-tool table_update --table-id <value> --title <value> --icon <value> --meta <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--title` | string | no | New table title (JSON string) |
| `--icon` | string | no | Table icon (emoji, e.g., "🎯") (JSON string) |
| `--meta` | string | no | Additional metadata dict (JSON string) |

### table_delete

Delete a table and all its data.

DESTRUCTIVE: This permanently deletes the table, all its fields,
and ALL RECORDS. This cannot be undone. Set confirm=True to proceed.

```bash
nocodb call-tool table_delete --table-id <value> --confirm
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--confirm` | boolean | no | Must be True to proceed with deletion |

### fields_list

List all fields in a table.

```bash
nocodb call-tool fields_list --table-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |

### field_get

Get detailed information about a field.

```bash
nocodb call-tool field_get --field-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--field-id` | string | yes | The field ID (e.g., "fld_xxx") |

### field_create

Create a new field in a table.

```bash
nocodb call-tool field_create --table-id <value> --title <value> --field-type <value> --options <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--title` | string | yes | The field title (e.g., "Status", "Email") |
| `--field-type` | string | yes | The field type (see list below) |
| `--options` | string | no | Optional field-specific options (JSON string) |

### field_update

Update a field's metadata.

Note: For updating SingleSelect/MultiSelect colors, use field_update_options instead.

```bash
nocodb call-tool field_update --field-id <value> --title <value> --options <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--field-id` | string | yes | The field ID (e.g., "fld_xxx") |
| `--title` | string | no | New field title (JSON string) |
| `--options` | string | no | New field options (not for colOptions updates) (JSON string) |

### field_update_options

Update a field's colOptions using v2 API.

Use this specifically for updating SingleSelect/MultiSelect choice colors,
which requires the v2 column update API.

```bash
nocodb call-tool field_update_options --field-id <value> --col-options <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--field-id` | string | yes | The field ID (e.g., "fld_xxx") |
| `--col-options` | object | yes | The colOptions dict with updated choices. Example for SingleSelect colors: {     "options": [         {"id": "opt_xxx", "title": "Active", "color": "#00FF00"},         {"id": "opt_yyy", "title": "Inactive", "color": "#FF0000"}     ] } (JSON string) |

### field_delete

Delete a field from a table.

DESTRUCTIVE: This permanently deletes the field and ALL DATA in that field
across all records. This cannot be undone. Set confirm=True to proceed.

```bash
nocodb call-tool field_delete --field-id <value> --confirm
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--field-id` | string | yes | The field ID (e.g., "fld_xxx") |
| `--confirm` | boolean | no | Must be True to proceed with deletion |

### linked_records_list

List records linked to a specific record via a Links field.

```bash
nocodb call-tool linked_records_list --table-id <value> --link-field-id <value> --record-id <value> --fields <value> --sort <value> --where <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID containing the link field (e.g., "tbl_xxx") |
| `--link-field-id` | string | yes | The Links field ID (e.g., "fld_xxx") |
| `--record-id` | string | yes | The record ID to get linked records for |
| `--fields` | string | no | Comma-separated field names to include from linked records (JSON string) |
| `--sort` | string | no | Sort field(s), prefix with - for descending (JSON string) |
| `--where` | string | no | Filter condition for linked records (JSON string) |

### linked_records_link

Link records together via a Links field.

Creates a relationship between the source record and target records.

```bash
nocodb call-tool linked_records_link --table-id <value> --link-field-id <value> --record-id <value> --target-ids <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID containing the link field (e.g., "tbl_xxx") |
| `--link-field-id` | string | yes | The Links field ID (e.g., "fld_xxx") |
| `--record-id` | string | yes | The source record ID to link from |
| `--target-ids` | array[string] | yes | List of record IDs to link to (e.g., ["1", "2", "3"]) |

### linked_records_unlink

Unlink records from a Links field relationship.

Removes the relationship between records. Does NOT delete the records themselves.

DESTRUCTIVE: Set confirm=True to proceed.

```bash
nocodb call-tool linked_records_unlink --table-id <value> --link-field-id <value> --record-id <value> --target-ids <value> --confirm
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID containing the link field (e.g., "tbl_xxx") |
| `--link-field-id` | string | yes | The Links field ID (e.g., "fld_xxx") |
| `--record-id` | string | yes | The source record ID to unlink from |
| `--target-ids` | array[string] | yes | List of record IDs to unlink (e.g., ["1", "2"]) |
| `--confirm` | boolean | no | Must be True to proceed with unlinking |

### views_list

List all views for a table.

Views include Grid, Gallery, Form, Kanban, and Calendar views.

```bash
nocodb call-tool views_list --table-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |

### view_update

Update a view's metadata.

```bash
nocodb call-tool view_update --view-id <value> --title <value> --icon <value> --meta <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |
| `--title` | string | no | New view title (JSON string) |
| `--icon` | string | no | View icon (emoji, e.g., "📊") (JSON string) |
| `--meta` | string | no | Additional metadata dict (JSON string) |

### view_delete

Delete a view.

This only deletes the view, not the underlying data.
Records remain intact.

```bash
nocodb call-tool view_delete --view-id <value> --confirm
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |
| `--confirm` | boolean | no | Must be True to proceed with deletion |

### view_filters_list

List all filters for a view.

```bash
nocodb call-tool view_filters_list --view-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |

### view_filter_get

Get details of a single filter.

```bash
nocodb call-tool view_filter_get --filter-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--filter-id` | string | yes | The filter ID (e.g., "flt_xxx") |

### view_filter_create

Create a new filter for a view.

```bash
nocodb call-tool view_filter_create --view-id <value> --fk-column-id <value> --comparison-op <value> --value <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |
| `--fk-column-id` | string | yes | The column/field ID to filter on (e.g., "fld_xxx") |
| `--comparison-op` | string | yes | The comparison operator |
| `--value` | string | no | The filter value (not needed for null/empty checks) (JSON string) |

### view_filter_update

Update an existing filter.

```bash
nocodb call-tool view_filter_update --filter-id <value> --fk-column-id <value> --comparison-op <value> --value <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--filter-id` | string | yes | The filter ID (e.g., "flt_xxx") |
| `--fk-column-id` | string | no | New column/field ID (JSON string) |
| `--comparison-op` | string | no | New comparison operator (JSON string) |
| `--value` | string | no | New filter value (JSON string) |

### view_filter_delete

Delete a filter from a view.

```bash
nocodb call-tool view_filter_delete --filter-id <value> --confirm
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--filter-id` | string | yes | The filter ID (e.g., "flt_xxx") |
| `--confirm` | boolean | no | Must be True to proceed with deletion |

### view_filter_children

Get children filters of a filter group.

Filter groups allow nested AND/OR logic.

```bash
nocodb call-tool view_filter_children --filter-group-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--filter-group-id` | string | yes | The parent filter group ID |

### view_sorts_list

List all sorts for a view.

```bash
nocodb call-tool view_sorts_list --view-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |

### view_sort_get

Get details of a single sort.

```bash
nocodb call-tool view_sort_get --sort-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--sort-id` | string | yes | The sort ID (e.g., "srt_xxx") |

### view_sort_create

Create a new sort for a view.

```bash
nocodb call-tool view_sort_create --view-id <value> --fk-column-id <value> --direction <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |
| `--fk-column-id` | string | yes | The column/field ID to sort by (e.g., "fld_xxx") |
| `--direction` | string | no | Sort direction - "asc" (ascending) or "desc" (descending) |

### view_sort_update

Update an existing sort.

```bash
nocodb call-tool view_sort_update --sort-id <value> --fk-column-id <value> --direction <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--sort-id` | string | yes | The sort ID (e.g., "srt_xxx") |
| `--fk-column-id` | string | no | New column/field ID (JSON string) |
| `--direction` | string | no | New sort direction - "asc" or "desc" (JSON string) |

### view_sort_delete

Delete a sort from a view.

```bash
nocodb call-tool view_sort_delete --sort-id <value> --confirm
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--sort-id` | string | yes | The sort ID (e.g., "srt_xxx") |
| `--confirm` | boolean | no | Must be True to proceed with deletion |

### view_columns_list

List all columns in a view with their visibility settings.

```bash
nocodb call-tool view_columns_list --view-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |

### view_column_update

Update a column's visibility or order in a view.

```bash
nocodb call-tool view_column_update --view-id <value> --column-id <value> --show <value> --order <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |
| `--column-id` | string | yes | The view column ID (from view_columns_list, not the field ID) |
| `--show` | string | no | Whether to show (True) or hide (False) the column (JSON string) |
| `--order` | string | no | Column position (0-indexed) (JSON string) |

### view_columns_hide_all

Hide all columns in a view.

Useful for starting fresh and then selectively showing specific columns.

```bash
nocodb call-tool view_columns_hide_all --view-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |

### view_columns_show_all

Show all columns in a view.

```bash
nocodb call-tool view_columns_show_all --view-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |

### shared_views_list

List all shared (public) views for a table.

```bash
nocodb call-tool shared_views_list --table-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |

### shared_view_create

Create a public link for a view.

This makes the view accessible via a unique URL without authentication.

```bash
nocodb call-tool shared_view_create --view-id <value> --password <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |
| `--password` | string | no | Optional password to protect the shared view (JSON string) |

### shared_view_update

Update a shared view's settings.

```bash
nocodb call-tool shared_view_update --view-id <value> --password <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |
| `--password` | string | no | New password (or None to remove password protection) (JSON string) |

### shared_view_delete

Remove public access from a view.

The public link will no longer work. The view itself is not deleted.

```bash
nocodb call-tool shared_view_delete --view-id <value> --confirm
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |
| `--confirm` | boolean | no | Must be True to proceed with removal |

### webhooks_list

List all webhooks for a table.

```bash
nocodb call-tool webhooks_list --table-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |

### webhook_delete

Delete a webhook.

```bash
nocodb call-tool webhook_delete --hook-id <value> --confirm
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--hook-id` | string | yes | The webhook ID (e.g., "hk_xxx") |
| `--confirm` | boolean | no | Must be True to proceed with deletion |

### webhook_logs

View execution logs for a webhook.

Useful for debugging webhook delivery issues.

```bash
nocodb call-tool webhook_logs --hook-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--hook-id` | string | yes | The webhook ID (e.g., "hk_xxx") |

### webhook_sample_payload

Get a sample webhook payload for testing.

```bash
nocodb call-tool webhook_sample_payload --table-id <value> --event <value> --operation <value> --version <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--event` | string | no | Event type - "records" (most common) |
| `--operation` | string | no | Operation type - "insert", "update", "delete" |
| `--version` | string | no | Payload version - "v1" or "v2" (default: "v2") |

### webhook_filters_list

List filters for a webhook.

Webhook filters determine when the webhook triggers based on field values.

```bash
nocodb call-tool webhook_filters_list --hook-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--hook-id` | string | yes | The webhook ID (e.g., "hk_xxx") |

### webhook_filter_create

Create a filter for a webhook.

Filters control when the webhook fires based on field values.

```bash
nocodb call-tool webhook_filter_create --hook-id <value> --fk-column-id <value> --comparison-op <value> --value <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--hook-id` | string | yes | The webhook ID (e.g., "hk_xxx") |
| `--fk-column-id` | string | yes | The column/field ID to filter on |
| `--comparison-op` | string | yes | The comparison operator (eq, neq, like, etc.) |
| `--value` | string | no | The filter value (JSON string) |

### members_list

List all members of the current base.

Returns:
    MembersListResult with list of members including id, email, and roles.

```bash
nocodb call-tool members_list
```

### member_add

Add a new member to the current base.

```bash
nocodb call-tool member_add --email <value> --role <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--email` | string | yes | The user's email address |
| `--role` | string | no | The role to assign. Options: - owner: Full control - creator: Can create tables - editor: Can edit records - commenter: Can comment only - viewer: Read-only access |

### member_update

Update a member's role.

```bash
nocodb call-tool member_update --member-id <value> --role <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--member-id` | string | yes | The member ID |
| `--role` | string | yes | The new role. Options: - owner: Full control - creator: Can create tables - editor: Can edit records - commenter: Can comment only - viewer: Read-only access |

### member_remove

Remove a member from the base.

The user will lose access to this base but their NocoDB account
is not affected.

```bash
nocodb call-tool member_remove --member-id <value> --confirm
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--member-id` | string | yes | The member ID to remove |
| `--confirm` | boolean | no | Must be True to proceed with removal |

### attachment_upload

Upload a file attachment to a record's Attachment field.

The file content must be provided as base64-encoded data.

```bash
nocodb call-tool attachment_upload --table-id <value> --record-id <value> --field-id <value> --filename <value> --content-base64 <value> --content-type <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |
| `--record-id` | string | yes | The record ID to attach the file to |
| `--field-id` | string | yes | The Attachment field ID (e.g., "fld_xxx") |
| `--filename` | string | yes | The filename for the uploaded file (e.g., "document.pdf") |
| `--content-base64` | string | yes | Base64-encoded file content |
| `--content-type` | string | yes | MIME type of the file (e.g., "application/pdf", "image/png") |

### storage_upload

Upload a file to NocoDB general storage.

This uploads a file to storage without attaching it to a specific record.
Useful for assets that need to be referenced across multiple records.

```bash
nocodb call-tool storage_upload --filename <value> --content-base64 <value> --content-type <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--filename` | string | yes | The filename (e.g., "logo.png", "document.pdf") |
| `--content-base64` | string | yes | Base64-encoded file content |
| `--content-type` | string | no | Optional MIME type (auto-detected if not provided) (JSON string) |

### export_csv

Export a view's data as CSV.

```bash
nocodb call-tool export_csv --view-id <value> --offset <value> --limit <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--view-id` | string | yes | The view ID (e.g., "vw_xxx") |
| `--offset` | string | no | Row offset for pagination (skip first N rows) (JSON string) |
| `--limit` | string | no | Maximum number of rows to export (JSON string) |

### schema_export_table

Export portable schema for a single table.

Returns a clean schema with system fields and internal IDs removed,
suitable for documentation or recreating the table structure.

```bash
nocodb call-tool schema_export_table --table-id <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--table-id` | string | yes | The table ID (e.g., "tbl_xxx") |

### schema_export_base

Export portable schema for the entire base with all tables.

Returns a clean schema with system fields and internal IDs removed,
suitable for documentation or recreating the base structure.

Returns:
    BaseSchemaResult with title, description, and tables array.
    Each table contains title and fields array.

Example output:
    {
        "title": "My Project",
        "description": "Project database",
        "tables": [
            {
                "title": "Users",
                "fields": [...]
            },
            {
                "title": "Tasks",
                "fields": [...]
            }
        ]
    }

```bash
nocodb call-tool schema_export_base
```

### list_resources

List all available resources and resource templates.

Returns JSON with resource metadata. Static resources have a
'uri' field, while templates have a 'uri_template' field with
placeholders like {name}.

```bash
nocodb call-tool list_resources
```

### read_resource

Read a resource by its URI.

For static resources, provide the exact URI. For templated
resources, provide the URI with template parameters filled in.

Returns the resource content as a string. Binary content is
base64-encoded.

```bash
nocodb call-tool read_resource --uri <value>
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--uri` | string | yes | The URI of the resource to read |

## Utility Commands

```bash
nocodb list-tools
nocodb list-resources
nocodb read-resource <uri>
nocodb list-prompts
nocodb get-prompt <name> [key=value ...]
```
