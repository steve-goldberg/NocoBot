# Contributing to nocodb-api-v3-client

We welcome contributions! However, we have strict guidelines to keep the codebase maintainable. Please read this entire document before submitting a PR.

## TL;DR

1. **Open an issue first** (required for all changes except docs/typos)
2. **Keep PRs small** - First-time contributors: max 5 files, 200 lines (tests/docs don't count)
3. **Use `/pr-overview`** in Claude Code to generate your PR description or simply write it like a human.
4. **One change per PR** - No bundling unrelated changes

---

## PR Size Limits

We enforce size limits to ensure quality reviews:

| Contributor Type | Max Files | Max Lines Changed |
|------------------|-----------|-------------------|
| First-time | 5 | 200 |
| Established (2+ merged PRs) | 15 | 500 |
| Large changes | Unlimited | Requires prior approval in issue |

**What doesn't count toward limits:**
- Test files (`*_test.py`) - we *want* you to write tests
- Documentation files (`*.md`) - we *want* you to update docs

**Why limits?** Small PRs get reviewed faster, have fewer bugs, and are easier to revert if needed.

---

## Auto-Rejection Criteria

Your PR will be automatically closed if:

- [ ] First-time PR exceeds 5 files or 200 lines (excluding tests/docs)
- [ ] No linked issue (except docs/typos)
- [ ] Missing required PR description sections
- [ ] No tests for code changes
- [ ] Unrelated changes bundled together
- [ ] Commit messages don't follow `type(scope): description` format

---

## Step-by-Step Contribution Process

### 1. Open an Issue First

**Required for:** Bug fixes, features, refactors, test additions

**Not required for:** Documentation fixes, typo corrections

Go to [Issues](../../issues) and create one using the appropriate template:
- **Bug Report** - For bugs you want to fix
- **Feature Request** - For new functionality

Wait for maintainer approval before starting work. This prevents wasted effort on changes we won't accept.

### 2. Fork and Clone

```bash
git clone https://github.com/YOUR-USERNAME/nocodb-api-v3-client.git
cd nocodb-api-v3-client
```

### 3. Set Up Development Environment

```bash
./init.sh
source venv/bin/activate
pip install -e ".[cli]"
```

### 4. Create a Branch

Branch names should be descriptive:

```bash
git checkout -b fix/double-wrap-record-id
git checkout -b feat/add-bulk-delete
git checkout -b docs/update-api-reference
```

### 5. Make Your Changes

Follow these rules:

- **One logical change per PR** - Don't fix a bug AND add a feature
- **Include tests** - Code changes require test coverage
- **Update docs** - If behavior changes, update README.md, CLAUDE.md, or skill.md
- **Follow existing patterns** - Look at similar code in the codebase

### 6. Run Tests

```bash
# Run all tests
python -m pytest nocodb/ -v

# Run specific test file
python -m pytest nocodb/filters/filters_test.py -v
```

All tests must pass before submitting.

### 7. Commit Your Changes

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `fix` - Bug fix
- `feat` - New feature
- `docs` - Documentation only
- `test` - Adding/updating tests
- `refactor` - Code restructure (no behavior change)
- `chore` - Maintenance tasks

**Scopes:**
- `api` - API client methods in `nocodb/api.py`
- `cli` - CLI commands in `nocodb/cli/`
- `filters` - Filter system in `nocodb/filters/`
- `infra` - HTTP client in `nocodb/infra/`
- `docs` - Documentation files

**Examples:**
```bash
git commit -m "fix(api): handle empty response in records_list_v3"
git commit -m "feat(cli): add --format flag for custom output"
git commit -m "docs: clarify v2 vs v3 API usage"
```

### 8. Generate PR Description

If you use Claude Code, run the `/pr-overview` skill to generate a detailed PR description:

```bash
claude "/pr-overview"
```

This analyzes your changes and generates a properly formatted description.

### 9. Submit Your PR

Push your branch and open a PR:

```bash
git push origin your-branch-name
```

Fill out the PR template completely. Incomplete PRs will be closed.

---

## Code Style

### Python

- Full type hints on all function signatures
- Docstrings for public functions (single line preferred)
- Follow existing patterns in the codebase
- Use `requests` for HTTP, `pytest` for tests

### Tests

- Colocate tests with source: `module.py` → `module_test.py`
- Use pytest fixtures and parametrize for variations
- Test both success and error cases

### Documentation

- Update `README.md` for user-facing changes
- Update `CLAUDE.md` for architecture/developer changes
- Update `nocodb/cli/skill.md` for CLI changes

---

## What Makes a Good PR

### Good PRs:

- Fix ONE specific bug with a test proving it's fixed
- Add ONE feature with tests and documentation
- Have clear commit messages explaining WHY
- Are small enough to review in 10 minutes

### Bad PRs:

- "Fixed some bugs and cleaned up code" (vague, bundled)
- 50 files changed with "Refactored everything" (too large)
- No tests, no docs, no issue reference (incomplete)
- Mix of unrelated changes (unfocused)

---

## Getting Help

- **Questions about contributing?** Open a Discussion
- **Found a bug?** Open an Issue using the Bug Report template
- **Want a feature?** Open an Issue using the Feature Request template

---

## Recognition

Contributors with merged PRs are recognized in the project. Quality over quantity - one well-crafted PR is worth more than ten sloppy ones.

Thank you for contributing!
