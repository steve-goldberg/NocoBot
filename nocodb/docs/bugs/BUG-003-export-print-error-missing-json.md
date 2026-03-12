# BUG-003: Export command missing as_json in print_error

## Status: open

## Summary
The `export csv` command does not pass `as_json=output_json` to `print_error()`, unlike every other CLI command. When `--json` flag is used and an error occurs, the output format is inconsistent (human text instead of JSON error object).

## Symptoms
- `nocodb export VIEW_ID --json` outputs plain text error instead of JSON error object on failure
- Breaks agent/scripted workflows that expect consistent JSON error format

## Steps to Reproduce
1. Run `nocodb export INVALID_VIEW_ID --json`
2. Expected: `{"success": false, "error": {"message": "..."}}`
3. Actual: Plain text error message

## Expected Behavior
Error output should respect `--json` flag like all other commands.

## Files to Investigate
| File | Reason |
|------|--------|
| `nocodb/cli/commands/export.py:65` | Missing `as_json=output_json` parameter |

## Investigation Log

### 2026-01-27 - Initial Report
- Reported by: grepai codebase audit
- Priority: medium
- Category: backend

## Resolution
Add `as_json=output_json` to the `print_error()` call in export.py.

## Changelog
[To be filled during fix]
