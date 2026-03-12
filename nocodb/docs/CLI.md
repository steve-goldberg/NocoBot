# Command-Line Interface

Auto-generated CLI via FastMCP with 62 commands mirroring the MCP server tools.

## Installation

```bash
pip install -e ".[cli]"
# or: uv pip install -e ".[cli]"
```

## Configuration

### Config File

Create `~/.nocodb.toml`:

```toml
url = "http://localhost:8080"
token = "YOUR-API-TOKEN"
```

### Environment Variables

```bash
export NOCODB_URL="http://localhost:8080"
export NOCODB_TOKEN="your-api-token"
```

## Commands

### Records

```bash
# List records
nocodb records list BASE_ID TABLE_ID

# With filtering and sorting
nocodb records list BASE_ID TABLE_ID --filter "(Status,eq,Active)" --sort "-CreatedAt"

# Get single record
nocodb records get BASE_ID TABLE_ID RECORD_ID

# Create record
nocodb records create BASE_ID TABLE_ID --data '{"Name": "New"}'

# Update record
nocodb records update BASE_ID TABLE_ID RECORD_ID --data '{"Status": "Done"}'

# Delete record
nocodb records delete BASE_ID TABLE_ID RECORD_ID

# Count records
nocodb records count BASE_ID TABLE_ID
```

### Bases & Tables

```bash
# List all bases
nocodb bases list

# List tables in a base
nocodb tables list BASE_ID

# Get table details
nocodb tables get BASE_ID TABLE_ID

# Create table
nocodb tables create BASE_ID --title "New Table"

# Delete table
nocodb tables delete BASE_ID TABLE_ID
```

### Fields

```bash
# List fields
nocodb fields list BASE_ID TABLE_ID

# Create single field
nocodb fields create BASE_ID TABLE_ID --title "Status" --type "SingleSelect"

# Batch create from JSON file
nocodb fields create BASE_ID TABLE_ID --file schema.json

# Delete single field
nocodb fields delete BASE_ID FIELD_ID

# Batch delete multiple fields
nocodb fields delete --ids "fld_xxx,fld_yyy"
```

### Linked Records

```bash
# List linked records
nocodb links list BASE_ID TABLE_ID LINK_FIELD_ID RECORD_ID

# Link records
nocodb links link BASE_ID TABLE_ID LINK_FIELD_ID RECORD_ID --targets 22,43

# Unlink records
nocodb links unlink BASE_ID TABLE_ID LINK_FIELD_ID RECORD_ID --targets 22
```

### Views

```bash
# List views
nocodb views list TABLE_ID

# Update view
nocodb views update VIEW_ID --title "New Name"

# Delete view
nocodb views delete VIEW_ID
```

### View Filters

```bash
# List filters
nocodb views filters list VIEW_ID

# Create filter
nocodb views filters create VIEW_ID --column COLUMN_ID --op eq --value "Active"

# Update filter
nocodb views filters update FILTER_ID --value "Inactive"

# Delete filter
nocodb views filters delete FILTER_ID
```

### View Sorts

```bash
# List sorts
nocodb views sorts list VIEW_ID

# Create sort
nocodb views sorts create VIEW_ID --column COLUMN_ID --direction asc

# Update sort
nocodb views sorts update SORT_ID --direction desc

# Delete sort
nocodb views sorts delete SORT_ID
```

### View Columns

```bash
# List columns
nocodb views columns list VIEW_ID

# Update column visibility/order
nocodb views columns update VIEW_ID COLUMN_ID --show --order 1

# Hide all columns
nocodb views columns hide-all VIEW_ID

# Show all columns
nocodb views columns show-all VIEW_ID
```

### Shared Views

```bash
# Create shared view (public link)
nocodb views share create VIEW_ID --password secret123

# List shared views
nocodb views share list TABLE_ID

# Update shared view
nocodb views share update VIEW_ID --password newpassword

# Delete shared view
nocodb views share delete VIEW_ID
```

### Export

```bash
# Export view to CSV (stdout)
nocodb export VIEW_ID

# Save to file
nocodb export VIEW_ID -o data.csv

# Limit rows
nocodb export VIEW_ID --limit 100
```

### Storage & Attachments

```bash
# Upload file to storage (general purpose)
nocodb storage upload ./document.pdf
nocodb storage upload ./image.png --content-type image/png

# Attach file to record field
nocodb attachments upload -t TABLE_ID -r RECORD_ID -f FIELD_ID ./photo.jpg
```

### Webhooks

```bash
# List webhooks
nocodb webhooks list TABLE_ID

# Delete webhook
nocodb webhooks delete HOOK_ID

# Get webhook logs
nocodb webhooks logs HOOK_ID

# Get sample payload
nocodb webhooks sample -t TABLE_ID --event records --operation insert

# Webhook filters
nocodb webhooks filters list HOOK_ID
nocodb webhooks filters create HOOK_ID --column FIELD_ID --op eq --value "test"
```

### Base Members

```bash
# List members
nocodb members list BASE_ID

# Add member
nocodb members add BASE_ID --email user@example.com --role editor

# Update role
nocodb members update BASE_ID USER_ID --role viewer

# Remove member
nocodb members remove BASE_ID USER_ID
```

### Schema Export

```bash
# Export table schema
nocodb schema table BASE_ID TABLE_ID

# Export entire base schema
nocodb schema base BASE_ID
```

## JSON Output

Use `--json` flag for machine-readable output:

```bash
# Pipe to jq for processing
nocodb records list BASE_ID TABLE_ID --json | jq '.records[].fields.Name'

# Get field IDs
nocodb fields list BASE_ID TABLE_ID --json | jq '.list[] | {title, id}'
```

## Troubleshooting

### Field Creation

- **SingleSelect/MultiSelect colors**: Use HEX codes (`#27ae60`), not named colors (`green`)
- **Links fields**: Use `--file` instead of `--options` to avoid shell escaping issues with nested JSON

### Common Issues

```bash
# Debug: check your config
nocodb --version
echo $NOCODB_URL
echo $NOCODB_TOKEN

# Verify connection
nocodb bases list
```

## Related Documentation

- [SDK](SDK.md) - Python client library
- [MCP Server](MCP.md) - AI assistant integration
- [Filters](FILTERS.md) - Query filter syntax
