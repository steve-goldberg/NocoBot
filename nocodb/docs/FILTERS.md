# Query Filters

Filter system for building NocoDB query conditions.

## Basic Usage

```python
from nocodb.filters import EqFilter, LikeFilter, And, Or, IsFilter, InFilter, BetweenFilter

# Simple filter - pass to params["where"]
result = client.records_list_v3(base_id, table_id, params={
    "where": EqFilter("Status", "Active").get_where()
})
# Generates: (Status,eq,Active)
```

## Comparison Filters

| Filter | Operator | Description | Example |
|--------|----------|-------------|---------|
| `EqFilter` | `eq` | Equal | `(Status,eq,Active)` |
| `EqualFilter` | `eq` | Equal (alias) | `(Status,eq,Active)` |
| `NotEqualFilter` | `neq` | Not equal | `(Status,neq,Draft)` |
| `GreaterThanFilter` | `gt` | Greater than | `(Age,gt,18)` |
| `GreaterOrEqualFilter` | `gte` | Greater than or equal | `(Age,gte,18)` |
| `LessThanFilter` | `lt` | Less than | `(Age,lt,65)` |
| `LessOrEqualFilter` | `lte` | Less than or equal | `(Age,lte,65)` |
| `LikeFilter` | `like` | Contains (use `%` wildcard) | `(Name,like,%test%)` |
| `NotLikeFilter` | `nlike` | Does not contain | `(Name,nlike,%test%)` |

### Examples

```python
from nocodb.filters import (
    EqFilter, NotEqualFilter, GreaterThanFilter,
    GreaterOrEqualFilter, LessThanFilter, LessOrEqualFilter,
    LikeFilter, NotLikeFilter
)

# Equal
EqFilter("Status", "Active").get_where()  # (Status,eq,Active)

# Not equal
NotEqualFilter("Status", "Draft").get_where()  # (Status,neq,Draft)

# Greater than
GreaterThanFilter("Age", 18).get_where()  # (Age,gt,18)

# Greater or equal
GreaterOrEqualFilter("Age", 18).get_where()  # (Age,gte,18)

# Less than
LessThanFilter("Age", 65).get_where()  # (Age,lt,65)

# Less or equal
LessOrEqualFilter("Age", 65).get_where()  # (Age,lte,65)

# Contains (like)
LikeFilter("Name", "%test%").get_where()  # (Name,like,%test%)

# Does not contain
NotLikeFilter("Name", "%test%").get_where()  # (Name,nlike,%test%)
```

## Special Filters

### IsFilter

Check for null, empty, and boolean values:

```python
from nocodb.filters import IsFilter

# Valid values: null, notnull, true, false, empty, notempty
IsFilter("Status", "notnull").get_where()   # (Status,is,notnull)
IsFilter("Name", "empty").get_where()       # (Name,is,empty)
IsFilter("Active", "true").get_where()      # (Active,is,true)
```

### InFilter

Match a list of values:

```python
from nocodb.filters import InFilter

InFilter("Tags", ["urgent", "important"]).get_where()  # (Tags,in,urgent,important)
InFilter("Status", ["Active", "Pending"]).get_where()  # (Status,in,Active,Pending)
```

### BetweenFilter

Range matching:

```python
from nocodb.filters import BetweenFilter

BetweenFilter("Age", 18, 65).get_where()  # (Age,btw,18,65)
BetweenFilter("Price", 10, 100).get_where()  # (Price,btw,10,100)
```

## Logical Operators

Combine filters using AND, OR, and NOT:

```python
from nocodb.filters import EqFilter, LikeFilter, And, Or, Not

# AND (v3 syntax: ~and)
And(
    EqFilter("Status", "Active"),
    LikeFilter("Name", "%test%")
).get_where()
# Generates: (Status,eq,Active)~and(Name,like,%test%)

# OR (v3 syntax: ~or)
Or(
    EqFilter("Status", "Active"),
    EqFilter("Status", "Pending")
).get_where()
# Generates: (Status,eq,Active)~or(Status,eq,Pending)

# NOT (v3 syntax: ~not)
Not(EqFilter("Status", "Draft")).get_where()
# Generates: ~not(Status,eq,Draft)
```

### Complex Combinations

```python
# Active users with "test" in name, OR any pending users
filter_condition = Or(
    And(
        EqFilter("Status", "Active"),
        LikeFilter("Name", "%test%")
    ),
    EqFilter("Status", "Pending")
)
# Generates: ((Status,eq,Active)~and(Name,like,%test%))~or(Status,eq,Pending)

# Use in query
result = client.records_list_v3(base_id, table_id, params={
    "where": filter_condition.get_where()
})
```

## Custom Filters

### Factory Function

Create custom filter classes:

```python
from nocodb.filters.factory import basic_filter_class_factory

# Create filter class for custom operator
CustomFilter = basic_filter_class_factory('custom_op')
my_filter = CustomFilter("field", "value")
my_filter.get_where()  # (field,custom_op,value)
```

### Raw Filter

Pass filter string directly:

```python
from nocodb.filters.raw_filter import RawFilter

# Use raw filter string
result = client.records_list_v3(base_id, table_id, params={
    "where": RawFilter('(field,op,value)').get_where()
})
```

## CLI Usage

Filter strings can be passed directly to CLI commands:

```bash
# Simple filter
nocodb records list BASE_ID TABLE_ID --filter "(Status,eq,Active)"

# Combined filter
nocodb records list BASE_ID TABLE_ID --filter "(Status,eq,Active)~and(Name,like,%test%)"

# With sorting
nocodb records list BASE_ID TABLE_ID --filter "(Status,eq,Active)" --sort "-CreatedAt"
```

## Related Documentation

- [SDK](SDK.md) - Python client library
- [CLI](CLI.md) - Command-line interface
