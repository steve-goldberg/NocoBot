# Command-Line Interface

Auto-generated CLI via `fastmcp generate-cli` with 62 commands mirroring the MCP server tools.

## Installation

```bash
pip install -e ".[cli]"
# or: uv pip install -e ".[cli]"
```

## Configuration

### Config File

Create `~/.nocodbrc` (TOML format):

```toml
[default]
url = "http://localhost:8080"
# token should be in NOCODB_TOKEN env var for security
# token = "your-api-token"
# base_id = "your-default-base-id"

# [profiles.prod]
# url = "https://nocodb.example.com"
# base_id = "prod_base_id"

# [profiles.dev]
# url = "http://localhost:8080"
# base_id = "dev_base_id"
```

Generate a starter config:

```bash
nocodb init
nocodb init --path /custom/path --force
```

Config can also be placed at `.nocodbrc` in the current directory (takes precedence over `~/.nocodbrc`), or set `NOCODB_CONFIG` to a custom path.

### Environment Variables

```bash
export NOCODB_URL="http://localhost:8080"
export NOCODB_TOKEN="your-api-token"
export NOCODB_BASE_ID="your-base-id"
export NOCODB_PROFILE="prod"  # optional, selects config profile
```

### Config Priority

1. CLI flags (`--url`, `--token`, `--base-id`)
2. Environment variables
3. Profile section from config file
4. Default section from config file

### Global Flags

```bash
nocodb --url http://localhost:8080 tables list
nocodb --token YOUR_TOKEN bases list
nocodb --base-id p_xxx tables list
nocodb --profile prod tables list
nocodb --config /path/to/.nocodbrc tables list
nocodb --version
```

## Commands

The CLI uses a `group command` pattern. All parameters are named flags (not positional args). Many commands read `base_id` from config/env rather than requiring it as a parameter.

### Records

```bash
# List records (paginated)
nocodb records list --table-id tbl_xxx

# With filtering and sorting
nocodb records list --table-id tbl_xxx --where "(Status,eq,Active)" --sort "-CreatedAt"

# With field selection and pagination
nocodb records list --table-id tbl_xxx --fields "Name,Email" --page 2 --page-size 50

# List all records (auto-paginates)
nocodb records list-all --table-id tbl_xxx --where "(Status,eq,Active)" --max-pages 10

# Get single record
nocodb records get --table-id tbl_xxx --record-id 1

# Create records (JSON array)
nocodb records create --table-id tbl_xxx --records '[{"Name": "New"}]'

# Update records (must include "id" in each object)
nocodb records update --table-id tbl_xxx --records '[{"id": 1, "Status": "Done"}]'

# Delete records (requires --force)
nocodb records delete --table-id tbl_xxx --record-ids 1 --record-ids 2 --force

# Count records
nocodb records count --table-id tbl_xxx --where "(Status,eq,Active)"
```

### Bases & Tables

```bash
# List all bases
nocodb bases list

# Get base info (uses configured base_id)
nocodb bases info

# List tables
nocodb tables list

# Get table details
nocodb tables get --table-id tbl_xxx

# Create table (with optional fields)
nocodb tables create --title "New Table"
nocodb tables create --title "Users" --fields '[{"title": "Name", "type": "SingleLineText"}]'

# Update table
nocodb tables update --table-id tbl_xxx --title "Renamed"

# Delete table (requires --force)
nocodb tables delete --table-id tbl_xxx --force
```

### Fields

```bash
# List fields
nocodb fields list --table-id tbl_xxx

# Get field details
nocodb fields get --field-id fld_xxx

# Create field
nocodb fields create --table-id tbl_xxx --title "Status" --field-type "SingleSelect" \
  --options '{"options": {"choices": [{"title": "Active", "color": "#27ae60"}]}}'

# Update field metadata
nocodb fields update --field-id fld_xxx --title "New Name"

# Update field colOptions (e.g., SingleSelect colors)
nocodb fields update-options --field-id fld_xxx \
  --col-options '{"options": [{"id": "opt_xxx", "title": "Active", "color": "#00FF00"}]}'

# Delete field (requires --force)
nocodb fields delete --field-id fld_xxx --force
```

### Linked Records

```bash
# List linked records
nocodb links list --table-id tbl_xxx --link-field-id fld_xxx --record-id 1

# Link records
nocodb links link --table-id tbl_xxx --link-field-id fld_xxx --record-id 5 \
  --target-ids 1 --target-ids 2 --target-ids 3

# Unlink records (requires --force)
nocodb links unlink --table-id tbl_xxx --link-field-id fld_xxx --record-id 5 \
  --target-ids 2 --force
```

### Views

```bash
# List views
nocodb views list --table-id tbl_xxx

# Update view
nocodb views update --view-id vw_xxx --title "New Name"

# Delete view (requires --force)
nocodb views delete --view-id vw_xxx --force
```

### View Filters

```bash
# List filters
nocodb filters list --view-id vw_xxx

# Get filter details
nocodb filters get --filter-id flt_xxx

# Create filter (uses field ID, not name)
nocodb filters create --view-id vw_xxx --fk-column-id fld_xxx --comparison-op eq --value "Active"

# Update filter
nocodb filters update --filter-id flt_xxx --value "Inactive"

# Delete filter (requires --force)
nocodb filters delete --filter-id flt_xxx --force

# Get children of a filter group
nocodb filters children --filter-group-id flt_xxx
```

### View Sorts

```bash
# List sorts
nocodb sorts list --view-id vw_xxx

# Get sort details
nocodb sorts get --sort-id srt_xxx

# Create sort
nocodb sorts create --view-id vw_xxx --fk-column-id fld_xxx --direction asc

# Update sort
nocodb sorts update --sort-id srt_xxx --direction desc

# Delete sort (requires --force)
nocodb sorts delete --sort-id srt_xxx --force
```

### View Columns

```bash
# List columns
nocodb columns list --view-id vw_xxx

# Update column visibility/order
nocodb columns update --view-id vw_xxx --column-id col_xxx --show true --order 1

# Hide all columns
nocodb columns hide-all --view-id vw_xxx

# Show all columns
nocodb columns show-all --view-id vw_xxx
```

### Shared Views

```bash
# Create shared view (public link)
nocodb shared create --view-id vw_xxx --password secret123

# List shared views
nocodb shared list --table-id tbl_xxx

# Update shared view
nocodb shared update --view-id vw_xxx --password newpassword

# Delete shared view (requires --force)
nocodb shared delete --view-id vw_xxx --force
```

### Export

```bash
# Export view to CSV
nocodb export csv --view-id vw_xxx

# With pagination
nocodb export csv --view-id vw_xxx --limit 100 --offset 200
```

### Storage & Attachments

```bash
# Upload file to storage (base64-encoded content)
nocodb storage upload --filename doc.pdf --content-base64 "..." --content-type application/pdf

# Attach file to record field (base64-encoded content)
nocodb attachments upload --table-id tbl_xxx --record-id 1 --field-id fld_xxx \
  --filename photo.jpg --content-base64 "..." --content-type image/jpeg
```

### Webhooks

```bash
# List webhooks
nocodb webhooks list --table-id tbl_xxx

# Delete webhook (requires --force)
nocodb webhooks delete --hook-id hk_xxx --force

# Get webhook logs
nocodb webhooks logs --hook-id hk_xxx

# Get sample payload
nocodb webhooks sample --table-id tbl_xxx --event records --operation insert

# List webhook filters
nocodb webhooks filters --hook-id hk_xxx

# Create webhook filter
nocodb webhooks filter-create --hook-id hk_xxx --fk-column-id fld_xxx --comparison-op eq --value "test"
```

### Base Members

```bash
# List members (uses configured base_id)
nocodb members list

# Add member
nocodb members add --email user@example.com --role editor

# Update role
nocodb members update --member-id usr_xxx --role viewer

# Remove member (requires --force)
nocodb members remove --member-id usr_xxx --force
```

### Schema Export

```bash
# Export table schema
nocodb schema table --table-id tbl_xxx

# Export entire base schema (uses configured base_id)
nocodb schema base
```

## Destructive Operations

Commands that delete or unlink data require `--force` (aliased to `--confirm` internally):

```bash
nocodb records delete --table-id tbl_xxx --record-ids 1 --force
nocodb tables delete --table-id tbl_xxx --force
nocodb fields delete --field-id fld_xxx --force
nocodb views delete --view-id vw_xxx --force
```

Without `--force`, destructive commands will refuse to execute.

## Command Shortcuts

```bash
# "list <resource>" and "get <resource>" work as shortcuts
nocodb list tables    # same as: nocodb tables list
nocodb get bases      # same as: nocodb bases info
```

## Troubleshooting

### Field Creation

- **SingleSelect/MultiSelect colors**: Use HEX codes (`#27ae60`), not named colors (`green`)
- **Links fields**: Use `--options` with JSON for nested options
- **Complex JSON**: Escape carefully or use single quotes around JSON values

### Common Issues

```bash
# Debug: check your config
nocodb --version

# Verify connection
nocodb bases list

# Check configured base
nocodb bases info
```

## Regenerating the CLI

After modifying MCP server tools, regenerate the CLI:

```bash
./scripts/regenerate-cli.sh
```

This is a custom script (not from fastmcp) that orchestrates the full regeneration:

1. **Start MCP server** — sources `.env`, finds an available port, launches `python -m nocodb.mcpserver --http` in the background
2. **Generate CLI** — calls `fastmcp generate-cli http://localhost:PORT/mcp` (the only fastmcp part) which introspects all MCP tools and writes `cli/generated.py` with a cyclopts command per tool
3. **Post-process** — inline Python rewrites the generated file:
   - Replaces the HTTP `CLIENT_SPEC` URL with a `StdioTransport` so the CLI spawns the MCP server as a subprocess instead of connecting over HTTP
   - Adds `os` and `StdioTransport` imports
   - Renames the app from `"localhost"` to `"nocodb"`
   - Fixes the module docstring
4. **Patch SKILL.md** — updates naming references if `cli/SKILL.md` exists
5. **Report** — counts and prints the number of generated tool commands

The generated CLI (`cli/generated.py`) is not meant to be edited by hand. The wrapper (`cli/wrapper.py`) sits in front of it and provides the user-facing command aliases (`records list` → `call-tool records_list`), parameter name translation (`--table-id` → `--table_id`), config injection, and `--force` → `--confirm` mapping.

## Related Documentation

- [SDK](SDK.md) - Python client library
- [MCP Server](MCP.md) - AI assistant integration
- [Filters](FILTERS.md) - Query filter syntax
