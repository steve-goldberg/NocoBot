# PR Overview Generator

Generate a detailed pull request description from your current git changes.

## Usage

Run this skill before submitting a PR:

```bash
claude "/pr-overview"
```

## What This Skill Does

1. Analyzes your git changes (staged and unstaged)
2. Validates PR size against contribution limits
3. Groups files by module/purpose
4. Generates a copy-paste ready PR description

## Workflow

### Step 1: Gather Git Information

Run these commands to understand the changes:

```bash
# See all changed files
git status

# Count lines changed
git diff --stat
git diff --cached --stat  # for staged changes

# See commits on this branch vs master
git log master..HEAD --oneline

# Get detailed diff
git diff
```

### Step 2: Validate PR Size

**What doesn't count toward limits:**
- Test files (`*_test.py`)
- Documentation files (`*.md`)

**First-time contributor limits (excluding tests/docs):**
- Maximum 5 files changed
- Maximum 200 lines changed (additions + deletions)

**Established contributor limits (2+ merged PRs, excluding tests/docs):**
- Maximum 15 files changed
- Maximum 500 lines changed

If the PR exceeds limits, suggest how to split it into smaller PRs.

### Step 3: Categorize Changes

Group changed files by module:

| Path Pattern | Module |
|--------------|--------|
| `nocodb/api.py` | API |
| `nocodb/cli/**` | CLI |
| `nocodb/filters/**` | Filters |
| `nocodb/infra/**` | Infrastructure |
| `*_test.py` | Tests |
| `*.md` | Documentation |
| `setup.py`, `pyproject.toml` | Build/Config |

### Step 4: Determine Change Type

Based on the changes, identify the type:

- `fix` - Bug fix (repairs broken behavior)
- `feat` - New feature (adds new capability)
- `docs` - Documentation only
- `test` - Tests only (no production code)
- `refactor` - Code restructure (no behavior change)
- `chore` - Maintenance (deps, configs, etc.)

### Step 5: Generate PR Description

Output this format:

```markdown
## Linked Issue

Closes #[NUMBER]
<!-- Or "N/A - documentation only" for docs PRs -->

## Summary

[1-2 sentence description of what changed and why]

## What Changed

- [Specific change 1]
- [Specific change 2]
- [Specific change 3]

## Files Changed (grouped by purpose)

**[Module Name]:**
- `path/to/file.py` - [Brief description of changes in this file]

**Tests:**
- `path/to/test.py` - [What tests were added/modified]

**Documentation:**
- `README.md` - [What doc changes were made]

## How to Test

1. [Step to verify the change works]
2. [Another verification step]

## PR Size

- **Files changed:** X
- **Lines added:** +Y
- **Lines removed:** -Z
- **Status:** [PASS] or [WARN: exceeds first-time limit]

## Checklist

- [ ] Tests pass locally (`pytest nocodb/ -v`)
- [ ] Added/updated tests for code changes
- [ ] Updated docs if needed
- [ ] Commit message follows `type(scope): description`
- [ ] PR is focused on ONE change
```

### Step 6: Validate and Warn

Check for common issues:

1. **No tests for code changes** - Warn that tests are required
2. **No linked issue** - Warn unless it's a docs-only change
3. **Mixed change types** - Suggest splitting the PR
4. **Commit message format** - Verify it follows `type(scope): description`

## Example Output

For a bug fix that changes 2 files:

```markdown
## Linked Issue

Closes #42

## Summary

Fix double-wrapping of record IDs in the delete command, which caused 404 errors when deleting records via CLI.

## What Changed

- Fixed record ID handling in delete command to not wrap already-wrapped IDs
- Added test case for the double-wrap scenario

## Files Changed (grouped by purpose)

**CLI:**
- `nocodb/cli/commands/records.py` - Remove redundant ID wrapping in delete handler

**Tests:**
- `nocodb/infra/requests_client_test.py` - Add test for delete with pre-wrapped ID

## How to Test

1. Run `nocodb records delete --base-id X --table-id Y --record-id 123`
2. Verify the record is deleted without 404 error
3. Run `pytest nocodb/ -v` to confirm all tests pass

## PR Size

- **Code files changed:** 1 (tests/docs don't count)
- **Code lines:** +12 / -3
- **Test/doc files:** 1 test file
- **Status:** [PASS] Within first-time contributor limits (5 files / 200 lines)

## Checklist

- [x] Tests pass locally (`pytest nocodb/ -v`)
- [x] Added/updated tests for code changes
- [x] Updated docs if needed
- [x] Commit message follows `type(scope): description`
- [x] PR is focused on ONE change
```

## Tips

- Run this skill AFTER you've made all your changes but BEFORE pushing
- If the skill warns about size limits, split your PR before submitting
- Copy the generated description directly into the GitHub PR form
- Double-check the linked issue number is correct
