---
name: nocodbv3
description: |
  NocoDB v3 CLI for database operations. Use when managing NocoDB bases, tables,
  fields, records, and relationships from the command line.
  Triggers: "nocodb", "create table", "add field", "link records", "database schema",
  "nocodb cli", "create database", "add column".
---

# NocoDB CLI

CLI for NocoDB v3 API. Self-hosted community edition.

## Setup

```bash
# Install
uv pip install git+https://github.com/steve-goldberg/nocodb-py.git

# Config (~/.nocodb.toml)
url = "http://localhost:8080"
token = "YOUR-API-TOKEN"

# Or env vars
export NOCODB_URL="http://localhost:8080"
export NOCODB_TOKEN="your-token"
```

## Core Workflow (Schema Creation)

```bash
# 1. List bases to get base ID
nocodb bases list --json

# 2. Create table with initial columns
nocodb tables create --title "Users" \
  -c '[{"title":"Name","type":"SingleLineText"},{"title":"Email","type":"Email"}]' \
  --json

# 3. Add more fields to table
nocodb fields create -t TABLE_ID --title "Age" --type Number --json

# 4. Create records
nocodb records create BASE_ID TABLE_ID --data '{"Name":"John","Email":"john@example.com"}'

# 5. Link records (for relationships)
nocodb links link BASE_ID TABLE_ID LINK_FIELD_ID RECORD_ID --targets 1,2,3
```

## Commands Quick Reference

### Bases
```bash
nocodb bases list                           # List all bases
nocodb bases list --json                    # JSON output
```

### Tables
```bash
nocodb tables list                          # List tables in base
nocodb tables get TABLE_ID                  # Get table details
nocodb tables create --title "Name"         # Create empty table
nocodb tables create --title "Name" -c '[{"title":"Col","type":"SingleLineText"}]'
nocodb tables update TABLE_ID --title "New" # Rename table
nocodb tables update TABLE_ID --icon "🎯"   # Set icon
nocodb tables delete TABLE_ID               # Delete table
```

### Fields
```bash
nocodb fields list -t TABLE_ID              # List fields
nocodb fields get FIELD_ID                  # Get field details
nocodb fields create -t TABLE_ID --title "Name" --type TYPE
nocodb fields create -t TABLE_ID --title "Status" --type SingleSelect \
  -o '{"options":{"choices":[{"title":"Active","color":"#00FF00"},{"title":"Inactive","color":"#FF0000"}]}}'
nocodb fields update FIELD_ID --title "New" # Rename field
nocodb fields update FIELD_ID -o '{"colOptions":{"options":[{"title":"A","color":"#ff0000","id":"ID"}]}}'  # Update colors
nocodb fields delete FIELD_ID               # Delete field
```

### Records
```bash
nocodb records list BASE TABLE              # List records
nocodb records list BASE TABLE --filter "(Status,eq,Active)" --sort "-CreatedAt"
nocodb records get BASE TABLE RECORD_ID     # Get single record
nocodb records create BASE TABLE --data '{"Name":"value"}'
nocodb records create BASE TABLE --data '[{"Name":"A"},{"Name":"B"}]'  # Batch
nocodb records update BASE TABLE RECORD_ID --data '{"Status":"Done"}'
nocodb records delete BASE TABLE RECORD_ID
```

### Links (Relationships)
```bash
nocodb links list BASE TABLE LINK_FIELD RECORD_ID
nocodb links link BASE TABLE LINK_FIELD RECORD_ID --targets 1,2,3
nocodb links unlink BASE TABLE LINK_FIELD RECORD_ID --targets 1
```

### Views
```bash
nocodb views list -t TABLE_ID               # List views
nocodb views update VIEW_ID --title "New"   # Rename view
nocodb views update VIEW_ID --icon "📊"     # Set icon

# Filters (full CRUD)
nocodb views filters list -v VIEW_ID        # List view filters
nocodb views filters create -v VIEW_ID --column COL_ID --op eq --value "X"
nocodb views filters update FILTER_ID --op neq --value "Y"
nocodb views filters delete FILTER_ID

# Sorts (full CRUD)
nocodb views sorts list -v VIEW_ID          # List view sorts
nocodb views sorts create -v VIEW_ID --column COL_ID --direction asc
nocodb views sorts update SORT_ID --direction desc
nocodb views sorts delete SORT_ID
```

### Attachments
```bash
nocodb attachments upload -t TABLE_ID -r RECORD_ID -f FIELD_ID --file /path/to/file.pdf
nocodb attachments upload -t TABLE_ID -r RECORD_ID -f FIELD_ID --file image.png --json
```

### Members
```bash
nocodb members list                         # List base members
nocodb members add --email "user@example.com" --role editor
nocodb members update MEMBER_ID --role viewer
nocodb members remove MEMBER_ID
```

### Export
```bash
nocodb export VIEW_ID                       # Print CSV to stdout
nocodb export VIEW_ID -o data.csv           # Save to file
nocodb export VIEW_ID --limit 100           # First 100 rows
nocodb export VIEW_ID --offset 50 --limit 50  # Rows 51-100
```

### Storage
```bash
nocodb storage upload ./document.pdf        # Upload file
nocodb storage upload ./image.png --content-type image/png
nocodb storage upload ./data.json --json    # JSON output
```

### View Columns
```bash
nocodb views columns list VIEW_ID           # List column visibility
nocodb views columns hide-all VIEW_ID       # Hide all columns
nocodb views columns show-all VIEW_ID       # Show all columns
nocodb views columns update VIEW_ID COL_ID --show --order 1
```

### Shared Views
```bash
nocodb views share list -t TABLE_ID         # List shared views
nocodb views share create VIEW_ID           # Create public link
nocodb views share create VIEW_ID --password secret123
nocodb views share update VIEW_ID --password newpass
nocodb views share delete VIEW_ID           # Remove public link
```

### Webhook Extras
```bash
nocodb webhooks logs HOOK_ID                # View webhook logs
nocodb webhooks sample -t TABLE_ID          # Get sample payload
nocodb webhooks sample -t TABLE_ID --event records --operation insert --version v2
nocodb webhooks filters list HOOK_ID        # List hook filters
nocodb webhooks filters create HOOK_ID --column FIELD_ID --op eq --value "test"
```

## Field Types

| Type | Description | Options Example |
|------|-------------|-----------------|
| `SingleLineText` | Short text | - |
| `LongText` | Multi-line text | - |
| `Number` | Integer | - |
| `Decimal` | Float | `{"precision":2}` |
| `Currency` | Money | `{"locale":"en-US","code":"USD"}` |
| `Percent` | Percentage | - |
| `Email` | Email address | - |
| `URL` | Web link | - |
| `PhoneNumber` | Phone | - |
| `Date` | Date only | `{"date_format":"YYYY-MM-DD"}` |
| `DateTime` | Date + time | - |
| `Time` | Time only | - |
| `Duration` | Time span | - |
| `Checkbox` | Boolean | - |
| `SingleSelect` | Dropdown | `{"options":{"choices":[{"title":"A","color":"#00FF00"}]}}` |
| `MultiSelect` | Multi-dropdown | `{"options":{"choices":[{"title":"A","color":"#00FF00"}]}}` |
| `Rating` | Star rating | `{"max":5}` |
| `Attachment` | File upload | - |
| `Links` | Relationship | See below |
| `Lookup` | Related field | - |
| `Rollup` | Aggregation | - |
| `Formula` | Calculated | `{"formula":"..."}` |

## Common Patterns

### Create Related Tables (One-to-Many)

```bash
# 1. Create parent table (Projects)
nocodb tables create --title "Projects" \
  -c '[{"title":"Name","type":"SingleLineText"}]' --json
# Note the table ID from response

# 2. Create child table (Tasks)
nocodb tables create --title "Tasks" \
  -c '[{"title":"Title","type":"SingleLineText"}]' --json

# 3. Add Links field to child table
nocodb fields create -t TASKS_TABLE_ID \
  --title "Project" \
  --type Links \
  -o '{"options":{"relation_type":"hm","related_table_id":"PROJECTS_TABLE_ID"}}' --json
```

### Create Table with All Common Fields

```bash
nocodb tables create --title "Contacts" -c '[
  {"title":"Name","type":"SingleLineText"},
  {"title":"Email","type":"Email"},
  {"title":"Phone","type":"PhoneNumber"},
  {"title":"Notes","type":"LongText"},
  {"title":"Status","type":"SingleSelect","dtxp":"Active,Inactive,Pending"},
  {"title":"Rating","type":"Rating"},
  {"title":"Active","type":"Checkbox"}
]' --json
```

### Bulk Import Records

```bash
nocodb records create BASE TABLE --data '[
  {"Name":"Alice","Email":"alice@example.com"},
  {"Name":"Bob","Email":"bob@example.com"},
  {"Name":"Carol","Email":"carol@example.com"}
]'
```

### Filter Records

```bash
# Equal
nocodb records list BASE TABLE --filter "(Status,eq,Active)"

# Like (contains)
nocodb records list BASE TABLE --filter "(Name,like,%john%)"

# Multiple conditions
nocodb records list BASE TABLE --filter "(Status,eq,Active)~and(Priority,eq,High)"

# Null check
nocodb records list BASE TABLE --filter "(Email,is,notnull)"
```

## JSON Output

All commands support `--json` for machine-readable output:

```bash
# Get table ID from create
TABLE_ID=$(nocodb tables create --title "Test" --json | jq -r '.id')

# Get field ID
FIELD_ID=$(nocodb fields list -t $TABLE_ID --json | jq -r '.list[0].id')

# Get record IDs
nocodb records list BASE TABLE --json | jq '.records[].id'
```

## Filter Operators

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

## Limitations (Self-Hosted)

| Feature | CLI | Notes |
|---------|-----|-------|
| Bases | list only | Cannot create bases via API |
| Tables | full CRUD | ✅ |
| Fields | full CRUD | ✅ |
| Records | full CRUD | ✅ |
| Links | list, link, unlink | ✅ |
| Attachments | upload | ✅ |
| Members | full CRUD | ✅ |
| Views | list, update, delete | Cannot create or get single view |
| View Columns | full CRUD | ✅ show/hide per view |
| Shared Views | full CRUD | ✅ public links with password |
| View Filters | full CRUD | ✅ |
| View Sorts | full CRUD | ✅ |
| Export CSV | export | ✅ async job-based |
| Storage | upload | ✅ general file uploads |
| Webhooks | list, delete | Cannot create/get/update/test |
| Webhook Logs | read | ✅ view execution logs |
| Webhook Filters | list, create | ✅ conditional triggers |

Use NocoDB web UI to create views and webhooks, then manage via CLI.

## Enterprise-Only Features (Not Available)

These features require NocoDB Enterprise and are **not supported** in self-hosted community edition:

| Feature | Reason |
|---------|--------|
| API Token Management | Token create/list/delete via API is Enterprise-only |
| Button Action Triggers | Trigger buttons via API is Enterprise-only |

**Note:** Button fields CAN be created via `fields create --type Button`, but button configuration (webhook ID, action type, formula) must be done in the NocoDB web UI. The trigger API returns 404 on self-hosted.
