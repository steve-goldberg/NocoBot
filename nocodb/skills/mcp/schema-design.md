---
name: schema-design
description: |
  Interactive NocoDB schema designer. Converts natural language descriptions
  into YAML schemas, iterates with user feedback, then builds tables using CLI.
  Invoke with /schema-design followed by what you want to build.
---

# /schema-design

Design and build NocoDB table schemas from natural language descriptions.

## Workflow

### Phase 1: Propose Schema

When user invokes `/schema-design [description]`:

1. Parse the natural language description
2. Identify entities (tables) and their relationships
3. Generate a YAML schema proposal
4. Present to user for review

### Phase 2: Iterate

When user provides feedback:
- "Add X field to Y table" → Update YAML, show again
- "Remove the Z field" → Update YAML, show again
- "Change X to SingleSelect with options A, B, C" → Update YAML, show again

Repeat until user approves with phrases like:
- "looks good"
- "build it"
- "create it"
- "approved"

### Phase 3: Build

When user approves, execute using `nocodb` CLI:

1. **Create tables first** (title only, to get IDs):
   ```bash
   nocodb tables create --title "TableName" --json
   ```
   Capture the `id` from JSON response for each table.

2. **Create non-Links fields** for each table:
   ```bash
   nocodb fields create -t TABLE_ID --title "FieldName" --type FieldType --json
   ```
   For SingleSelect/MultiSelect, use `--file` with JSON:
   ```bash
   echo '[{"title":"Status","type":"SingleSelect","options":{"choices":[{"title":"Active","color":"#27ae60"}]}}]' > /tmp/field.json
   nocodb fields create -t TABLE_ID --file /tmp/field.json --json
   ```

3. **Create Links fields last** (need all table IDs):
   ```bash
   nocodb fields create -t TABLE_ID --title "Related" --type Links \
     --options '{"relation_type":"mm","related_table_id":"OTHER_TABLE_ID"}' --json
   ```

4. **Report results**:
   - On success: "Created X tables with Y fields"
   - On error: Stop, show which table/field failed, show error message

## YAML Schema Format

```yaml
tables:
  - name: Contacts
    fields:
      - name: Name
        type: SingleLineText
        primary: true
      - name: Email
        type: Email
        required: true
      - name: Status
        type: SingleSelect
        choices:
          - Active
          - Inactive
          - Lead
      - name: Company
        type: Links
        link_to: Companies
        relation: mm

  - name: Companies
    fields:
      - name: Name
        type: SingleLineText
        primary: true
      - name: Website
        type: URL
```

## Field Properties

| Property | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Field title |
| `type` | Yes | NocoDB field type (see below) |
| `primary` | No | Mark as primary display field |
| `required` | No | Not null constraint |
| `choices` | No | Options for SingleSelect/MultiSelect |
| `link_to` | No | Target table name (for Links type) |
| `relation` | No | `hm` (has-many) or `mm` (many-to-many) |

## Field Types

| Type | Description |
|------|-------------|
| `SingleLineText` | Short text (default for primary) |
| `LongText` | Multi-line text |
| `Number` | Integer |
| `Decimal` | Float |
| `Currency` | Money |
| `Percent` | Percentage |
| `Email` | Email address |
| `URL` | Web link |
| `PhoneNumber` | Phone |
| `Date` | Date only |
| `DateTime` | Date + time |
| `Checkbox` | Boolean |
| `SingleSelect` | Dropdown (use `choices`) |
| `MultiSelect` | Multi-select (use `choices`) |
| `Rating` | Star rating |
| `Attachment` | File upload |
| `Links` | Relationship (use `link_to`, `relation`) |

## Example Interaction

```
User: /schema-design I need a simple task tracker with projects and tasks

Claude: Here's a proposed schema:

tables:
  - name: Projects
    fields:
      - name: Name
        type: SingleLineText
        primary: true
      - name: Description
        type: LongText
      - name: Status
        type: SingleSelect
        choices:
          - Planning
          - Active
          - Completed

  - name: Tasks
    fields:
      - name: Title
        type: SingleLineText
        primary: true
      - name: Description
        type: LongText
      - name: Status
        type: SingleSelect
        choices:
          - Todo
          - In Progress
          - Done
      - name: Due Date
        type: Date
      - name: Project
        type: Links
        link_to: Projects
        relation: hm

Would you like any changes?

User: Add a Priority field to Tasks with High, Medium, Low options

Claude: Updated:

tables:
  - name: Projects
    ...

  - name: Tasks
    fields:
      - name: Title
        type: SingleLineText
        primary: true
      - name: Description
        type: LongText
      - name: Priority
        type: SingleSelect
        choices:
          - High
          - Medium
          - Low
      - name: Status
        type: SingleSelect
        choices:
          - Todo
          - In Progress
          - Done
      - name: Due Date
        type: Date
      - name: Project
        type: Links
        link_to: Projects
        relation: hm

Ready to build?

User: Build it

Claude: [executes CLI commands]
Creating tables...
  ✓ Projects (tbl_abc123)
  ✓ Tasks (tbl_def456)
Creating fields...
  ✓ Projects.Name
  ✓ Projects.Description
  ✓ Projects.Status
  ✓ Tasks.Title
  ✓ Tasks.Description
  ✓ Tasks.Priority
  ✓ Tasks.Status
  ✓ Tasks.Due Date
Creating relationships...
  ✓ Tasks.Project → Projects

Done! Created 2 tables with 9 fields.
```

## Notes

- Colors for SingleSelect/MultiSelect choices are auto-assigned
- Links fields create the relationship in both directions
- Build stops on first error - fix YAML and try again
- This skill creates new tables only (no updates to existing)
