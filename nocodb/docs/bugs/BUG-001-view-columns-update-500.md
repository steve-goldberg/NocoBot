# BUG-001: View Columns Update Returns 500 Error

## Status: open

## Summary

The NocoDB v2 API endpoint `PATCH /api/v2/meta/views/{viewId}/columns/{columnId}` returns a 500 Internal Server Error when attempting to update individual column visibility settings. This is a server-side bug in NocoDB's self-hosted community edition, not a client-side issue.

## Symptoms

- `views columns update` CLI command fails with 500 error
- `view_column_update()` SDK method returns HTTP 500
- Individual column hide/show operations fail
- All other view column operations work correctly:
  - `view_columns_list()` - works
  - `view_columns_hide_all()` - works
  - `view_columns_show_all()` - works

## Steps to Reproduce

1. Create a view in NocoDB (Grid, Kanban, Gallery, or Calendar)
2. Get the view ID and a column ID from `views columns list`
3. Attempt to update column visibility:

```bash
# This fails with 500 error
nocodb views columns update vw_xxx col_yyy --hide

# Or via SDK
client.view_column_update("vw_xxx", "col_yyy", {"show": False})
```

4. **Expected**: Column visibility updated
5. **Actual**: HTTP 500 Internal Server Error

## Expected Behavior

The endpoint should accept a JSON body like `{"show": false}` or `{"order": 5}` and update the view column settings, returning the updated column object.

## Environment

- NocoDB: Self-hosted community edition
- API Version: v2 (`/api/v2/meta/views/{viewId}/columns/{columnId}`)
- Client: nocodb-api-v3-client v3.0.0

## Hypotheses

- [x] NocoDB v2 API bug in self-hosted community edition (most likely)
- [ ] Endpoint may require enterprise/cloud features
- [ ] API may have changed in recent NocoDB versions
- [ ] Specific payload format required that differs from documentation

## Files to Investigate

| File | Reason |
|------|--------|
| [nocodb/infra/requests_client.py](../../nocodb/infra/requests_client.py) | `view_column_update()` implementation at line 1614 |
| [nocodb/api.py](../../nocodb/api.py) | `get_view_column_uri()` URI builder at line 410 |
| [nocodb/cli/commands/views.py](../../nocodb/cli/commands/views.py) | CLI `columns update` command at line 507 |

## Working Alternatives

While the individual column update is broken, these operations work:

```bash
# Hide ALL columns in a view
nocodb views columns hide-all vw_xxx

# Show ALL columns in a view
nocodb views columns show-all vw_xxx

# List columns to see current visibility
nocodb views columns list vw_xxx
```

Or configure column visibility through the NocoDB web UI.

## Related Features

- View Columns API (v2)
- Column visibility management

## Investigation Log

### 2026-01-24 - Initial Report

- Reported by: User
- Priority: medium (3)
- Category: integration
- Classification: **External bug** - NocoDB server returns 500, not a client issue

### API Verification

The client implementation follows the documented v2 API:
- Endpoint: `PATCH /api/v2/meta/views/{viewId}/columns/{columnId}`
- Body: `{"show": true/false}` or `{"order": number}`
- URI builder correctly constructs path in `api.py:410`
- Client method correctly sends PATCH request in `requests_client.py:1614`

## Resolution

**Upstream bug**: This requires a fix in NocoDB itself. The client implementation is correct per the API documentation.

**Workarounds available**:
1. Use `hide-all` / `show-all` for bulk operations
2. Use NocoDB UI for individual column visibility changes

## Changelog

- 2026-01-24: Bug documented, classified as external NocoDB server bug
