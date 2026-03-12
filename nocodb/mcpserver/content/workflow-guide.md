# NocoDB Workflow Guide

## STOP! Before ANY Query Operation

**Did you call `fields_list` yet?**

If you're about to use `sort` or `where` parameters, you MUST know the exact field names first.
The API returns 400 Bad Request if you use field names that don't exist or have wrong case.

---

## Required Workflow

```
1. tables_list              -> Get table IDs
2. fields_list(table_id)    -> REQUIRED before sort/where - get exact field names
3. records_list(...)        -> Query using actual field names from step 2
```

---

## Field Name Rules

- **Case-sensitive**: "Status" != "status" != "STATUS"
- **Must match exactly** as returned by fields_list
- **Never guess** - always discover first
- **Use display names**, not database column names

---

## Example

```python
# WRONG - Guessing field names (will fail with 400)
records_list(table_id="tbl_xxx", sort="-plays")
records_list(table_id="tbl_xxx", where="(status,eq,Active)")

# CORRECT - Discover then use
fields_list(table_id="tbl_xxx")
# Returns: Title, Plays, Views, Status, CreatedAt, ...

records_list(table_id="tbl_xxx", sort="-Plays")  # Exact case!
records_list(table_id="tbl_xxx", where="(Status,eq,Active)")  # Exact case!
```

---

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `400 Bad Request` on sort/where | Field name doesn't exist or wrong case | Call `fields_list` first, use exact names |
| `400 Bad Request` with field_id | Using display name instead of field ID | Use `fld_xxx` format from `fields_list` |
| Empty results with valid filter | Field name typo or case mismatch | Verify field name with `fields_list` |

---

## Anti-Patterns (Things That Will Fail)

- Guessing field names: `sort="-plays"` -> use `fields_list` first!
- Using database column names: `where="(created_at,gt,2024)"` -> use display names
- Lowercase field names: `where="(status,eq,active)"` -> check exact case
- Assuming standard names: `sort="-id"` -> ID might be "Id" or "ID" or "nc_id"

---

## Troubleshooting

### My query returned 400 Bad Request
1. Did you call `fields_list` first? (No excuses!)
2. Did you copy the field name EXACTLY as returned?
3. Check capitalization - field names are case-sensitive

### My query returned empty results
1. Verify your `where` clause uses exact field names
2. Test without filters first to confirm records exist
3. Check if you're using the right table_id
