# MCP Server

FastMCP 3.0 server exposing 62 tools + 2 prompts for AI assistants like Claude Desktop.

## Installation

```bash
pip install -e ".[mcp]"
# or: uv pip install -e ".[mcp]"
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NOCODB_URL` | Yes | NocoDB server URL |
| `NOCODB_TOKEN` | Yes | API token or JWT |
| `NOCODB_BASE_ID` | Yes | Base ID to work with |
| `NOCODB_VERIFY_SSL` | No | Set to `false` for self-signed certs |

## Local Usage (stdio)

Configure in `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nocodb": {
      "command": "/bin/bash",
      "args": ["-c", "source /path/to/.env && python3 -m nocodb.mcpserver"],
      "env": {
        "NOCODB_URL": "http://localhost:8080",
        "NOCODB_TOKEN": "your-api-token",
        "NOCODB_BASE_ID": "your-base-id"
      }
    }
  }
}
```

## Remote Deployment (HTTP)

### Docker

```bash
# Build
docker build -t nocodb-mcp .

# Run
docker run -p 8000:8000 \
  -e NOCODB_URL=https://your-nocodb.com \
  -e NOCODB_TOKEN=your-token \
  -e NOCODB_BASE_ID=your-base-id \
  -e NOCODB_VERIFY_SSL=false \
  nocodb-mcp
```

### Dokploy

See [DEPLOY_MCP.md](DEPLOY_MCP.md) for full deployment guide.

### Connect Claude Desktop to Remote Server

Use mcp-remote bridge:

```json
{
  "mcpServers": {
    "nocodb-remote": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://your-server/mcp", "--allow-http"]
    }
  }
}
```

**Note:** The `--allow-http` flag is required for non-HTTPS URLs (e.g., internal networks, Tailscale).

## Available Tools

### Records (6 tools)
- `records_list` - List records with filtering/sorting
- `record_get` - Get single record by ID
- `records_create` - Create records (batch)
- `records_update` - Update records (batch)
- `records_delete` - Delete records (batch)
- `records_count` - Count records

### Tables (5 tools)
- `tables_list` - List tables in base
- `table_get` - Get table schema
- `table_create` - Create table
- `table_update` - Update table
- `table_delete` - Delete table

### Fields (6 tools)
- `fields_list` - List fields in table
- `field_get` - Get field details
- `field_create` - Create field
- `field_update` - Update field
- `field_update_options` - Update field column options
- `field_delete` - Delete field

### Links (3 tools)
- `linked_records_list` - List linked records
- `link` - Link records
- `unlink` - Unlink records

### Bases (2 tools)
- `bases_list` - List all bases
- `base_info` - Get base details

### Views (3 tools)
- `views_list` - List views for table
- `view_update` - Update view
- `view_delete` - Delete view

### View Filters (4 tools)
- `view_filters_list` - List filters
- `view_filter_create` - Create filter
- `view_filter_update` - Update filter
- `view_filter_delete` - Delete filter

### View Sorts (4 tools)
- `view_sorts_list` - List sorts
- `view_sort_create` - Create sort
- `view_sort_update` - Update sort
- `view_sort_delete` - Delete sort

### View Columns (4 tools)
- `view_columns_list` - List columns
- `view_column_update` - Update column
- `view_columns_hide_all` - Hide all columns
- `view_columns_show_all` - Show all columns

### Shared Views (4 tools)
- `shared_views_list` - List shared views
- `shared_view_create` - Create shared view
- `shared_view_update` - Update shared view
- `shared_view_delete` - Delete shared view

### Webhooks (5 tools)
- `webhooks_list` - List webhooks
- `webhook_delete` - Delete webhook
- `webhook_logs` - Get webhook logs
- `webhook_sample` - Get sample payload
- `webhook_filters_list` - List webhook filters

### Members (4 tools)
- `members_list` - List base members
- `member_add` - Add member
- `member_update` - Update member role
- `member_remove` - Remove member

### Attachments (1 tool)
- `attachment_upload` - Upload attachment to record field

### Storage (1 tool)
- `storage_upload` - Upload file to storage

### Export (1 tool)
- `export_csv` - Export view to CSV

### Schema (2 tools)
- `schema_export_table` - Export table schema
- `schema_export_base` - Export base schema

### Docs (2 tools)
- `get_workflow_guide` - Get workflow documentation
- `get_reference` - Get complete reference docs

## Available Prompts

### nocodb_workflow

Critical rules for schema discovery. Should be called before using sort/where parameters to understand field names and IDs.

### nocodb_reference

Complete reference documentation for all tools, including parameter details and examples.

## HTTP Endpoints

When running in HTTP mode:

| Endpoint | Description |
|----------|-------------|
| `/mcp` | Streamable HTTP MCP endpoint |
| `/health` | Health check for load balancers |

## Related Documentation

- [SDK](SDK.md) - Python client library
- [CLI](CLI.md) - Command-line interface
- [Dokploy Deployment](DEPLOY_MCP.md) - Full deployment guide
