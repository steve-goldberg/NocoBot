# TASK-001: Remove v1 Legacy API Code

## Status: completed

## Summary

Remove deprecated v1 API code that is no longer used. The client has fully migrated to v2/v3 APIs, and the v1 code paths are dead code that should be cleaned up to reduce maintenance burden and confusion.

## Scope

### File 1: `nocodb/api.py`

**Remove constants:**
- `V1_DB_DATA_PREFIX`
- `V1_DB_META_PREFIX`

**Remove attributes:**
- `__base_data_uri_v1`
- `__base_meta_uri_v1`

**Remove deprecated v1 methods:**
- `get_table_uri()`
- `get_row_detail_uri()`
- `get_bulk_rows_uri()`
- `get_nested_relations_uri()`
- `get_projects_uri()`
- `get_tables_uri()`
- `get_column_uri()`

### File 2: `nocodb/infra/requests_client.py`

**Remove v1 methods that use deprecated URIs:**
- `table_column_update()` - uses v1 `get_column_uri`
- `table_column_delete()` - uses v1 `get_column_uri`
- `table_column_set_primary()` - uses v1 `get_column_uri`

### File 3: `nocodb/nocodb.py`

**Update:**
- Remove/update docstrings mentioning v1 API
- Remove `NocoDBProject` class (v1 compatibility alias)

## Checklist

- [x] Verify no code references v1 methods before removal
- [x] Remove v1 constants from `api.py`
- [x] Remove v1 attributes from `api.py`
- [x] Remove v1 URI methods from `api.py`
- [x] Remove v1 column methods from `requests_client.py`
- [x] Remove `NocoDBProject` from `nocodb.py`
- [x] Update docstrings in `nocodb.py`
- [x] Update `__init__.py` exports if needed
- [x] Run tests to verify nothing breaks
- [x] Update CLAUDE.md if it references v1 (not needed - no v1 references)

## Pre-Removal Verification

Before removing, grep for usages:
```bash
# Check for v1 method usage
grep -r "get_table_uri\|get_row_detail_uri\|get_bulk_rows_uri" nocodb/
grep -r "get_nested_relations_uri\|get_projects_uri\|get_tables_uri" nocodb/
grep -r "get_column_uri" nocodb/
grep -r "table_column_update\|table_column_delete\|table_column_set_primary" nocodb/
grep -r "NocoDBProject" nocodb/
```

## Risk Assessment

**Low risk** - These are deprecated code paths:
- v1 API is no longer used by NocoDB
- All current functionality uses v2/v3 APIs
- Tests should pass after removal

## Related

- Client migrated to v2/v3 hybrid approach in v3.0.0
- See MIGRATION.md for API version reference

## Created

- Date: 2026-01-24
- Priority: low (cleanup task)
- Category: refactoring
