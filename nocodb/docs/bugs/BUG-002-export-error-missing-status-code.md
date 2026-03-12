# BUG-002: NocoDBAPIError missing required status_code in export

## Status: open

## Summary
The `export_view()` method raises `NocoDBAPIError` with only a message string, but the exception class requires `status_code` as a mandatory positional argument. This causes a `TypeError` at runtime when an export job fails or times out.

## Symptoms
- `nocodb export VIEW_ID` crashes with `TypeError` instead of a helpful error when export fails
- `TypeError: NocoDBAPIError.__init__() missing 1 required positional argument: 'status_code'`
- Export timeout and export failure both trigger this bug

## Steps to Reproduce
1. Trigger a failed export job (e.g., invalid view ID that passes initial validation but fails server-side)
2. Or wait for export timeout (300s)
3. Expected: descriptive error message
4. Actual: `TypeError` from exception constructor

## Expected Behavior
Should raise `NocoDBAPIError` with both message and status_code, or use a different exception type.

## Files to Investigate
| File | Reason |
|------|--------|
| `nocodb/infra/requests_client.py:1346-1347` | First broken raise (export job failed) |
| `nocodb/infra/requests_client.py:1353` | Second broken raise (export timeout) |
| `nocodb/exceptions.py:8` | Exception class definition requiring status_code |

## Investigation Log

### 2026-01-27 - Initial Report
- Reported by: grepai codebase audit
- Priority: critical (will crash at runtime)
- Category: backend

## Resolution
Add `status_code` parameter to both `NocoDBAPIError` raises. Use `0` or `500` for non-HTTP errors (timeout/job failure), or switch to a plain `RuntimeError`.

## Changelog
[To be filled during fix]
