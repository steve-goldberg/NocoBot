# Phase 3 — Migrate to FastMCP 4.x

**Agent:** `nocodb-phase-3`
**Prerequisite reading:** `nocodb/docs/upgrade/FASTMCP4-UPGRADE-REPORT.md` — read it **in full** first.
**Depends on:** Phases 0, 1, and 2 committed. Do not start otherwise.
**This is the phase that actually changes the version.**

---

## Why this is smaller than it looks

Report §3.2: a repo-wide grep for every removed or changed FastMCP API returned **zero hits** —
`ctx.sample`, `ctx.elicit`, `ctx.list_roots`, `ctx.set_state`, `import_server`, `as_proxy`,
`serializer=`, `exclude_args=`, `McpError(`, `except httpx`, `decorator_mode`, `task=True`,
`add_tool_transformation`, `remove_tool(`, `on_initialize`, and every moved module path.

Report §3.3: everything structural **survives** — `@mcp.tool`, `@mcp.resource`, the
`@asynccontextmanager` lifespan, `ResourcesAsTools` + `add_transform`, `custom_route("/health")`,
`mcp.run(transport="http", ...)`, `ToolError`, and `DebugTokenVerifier(validate=, client_id=)`.

**The migration is 8 camelCase reads plus dependency floors.** Do not refactor architecture. If you
find yourself redesigning something, stop and escalate.

Root cause of the breaks: FastMCP 4 sits on MCP Python SDK v2, which renamed every protocol model
field camelCase → snake_case (`inputSchema` → `input_schema`, `isError` → `is_error`). **The wire
format is unchanged** (`fastmcp-full.txt:32451`).

---

## Scope

### 1. Fix `nocobot` — the hard break, no compat bridge

Report §4.1. `nocobot` imports **only the raw MCP SDK** and **never imports fastmcp**, so FastMCP's
camelCase compatibility bridge explicitly does **not** cover it (scope limit at
`fastmcp-full.txt:32557`).

| Site | Current | Fix |
|---|---|---|
| `nocobot/mcp_client.py:162` | `result.isError` | `result.is_error` |
| `nocobot/mcp_client.py:103` | `tool.inputSchema if hasattr(tool, 'inputSchema') else {}` | see below |

**Line 103 is the most dangerous defect in this repo and the fix is NOT to repoint the guard at
`input_schema`.** Under SDK v2 the `hasattr` check evaluates False and ships `{}` as every tool's
parameter schema to the LLM. It does not crash; the agent silently degrades to guessing at
parameters, surfacing days later as "the bot got worse" with no error trail.

**Delete the fallback.** A tool with no input schema is an error worth raising, not a `{}` worth
shipping. This is the Fail Fast rule in `~/.claude/CLAUDE.md` — no silent fallbacks that mask
failures. Phase 1's T3 asserts every tool has a non-empty schema, so a raise here is backed by a
test that proves the condition never legitimately occurs.

Then grep `nocobot/` for any other camelCase protocol reads: `structuredContent`, `mimeType`,
`nextCursor`, `serverInfo`, `protocolVersion`, `resourceTemplates`, `uriTemplate`, `hasMore`.

### 2. Fix / regenerate `nocodb/cli/generated.py`

Report §4.2. Sites: `:56` `block.mimeType`, `:59`, `:91-92` `tool.inputSchema`, `:133`, `:177`
`msg.content.mimeType`. This file **does** `from fastmcp import Client` (`:16`), so these are
bridged-with-warning rather than fatal.

**Report §4.2 marks the bridge UNVERIFIED — verify it empirically before relying on it.** Then
regenerate under 4.x via the Phase-2-hardened `regenerate-cli.sh`. If the generator now emits
snake_case natively, the regenerated file needs no patching. If the hardened script now fails on a
changed template, that is the script doing its job — fix the patterns, do not disable the assertions.

Expected: still **63** commands.

### 3. Raise the dependency floors

In `nocodb/setup.py`, at all three sites (47, 51, 54): lift Phase 0's `,<4` cap and move to
`fastmcp>=4`. Remove the "capped pending migration" comments Phase 0 added.

Also (report §3.1):
- `pydantic>=2.12` is the new floor (B2). venv already has 2.12.5, but the *declared* floor must
  move — check `nocobot/pyproject.toml:23` (`pydantic>=2.0.0`).
- `starlette>=1.0.1` (B3) will be pulled by the fastmcp server extra; confirm it resolves.
- FastAPI is **not used** in this repo (B4 N/A). httpx→httpx2 (B5) is **N/A** — zero `except httpx.`
  hits. Do not chase either.

**Consider capping at `<5`** rather than leaving `>=4` unbounded. Report §3.4 notes FastMCP 5 already
has removals scheduled (bare-string `Client("server.py")`). Leaving it unbounded rebuilds exactly
the exposure Phase 0 just closed. State your reasoning either way.

### 4. Add a lockfile and lock the Docker build

This is the durable fix for the exposure that made Phase 0 urgent. Report §2.3 / §2.4.

`nocodb/` has **no lockfile at all** and `nocodb/Dockerfile:10` runs
`uv pip install --system -e ".[mcp]"` against live PyPI on every build.

Port the known-good pattern from `nocobot/Dockerfile` (report §2.3):
- `COPY` the manifest + lock, then `uv export --locked --no-dev --no-hashes > /tmp/requirements.txt`
- `uv pip install --system --no-cache -r /tmp/requirements.txt`
- `uv pip install --system --no-cache --no-deps .`

`--locked` fails the build if the lock drifts from the manifest; `--no-deps` on the final install
stops the resolver re-widening.

Constraint to respect: the build context **must** remain `nocodb/` — required by the `package_dir`
mapping (`setup.py:20-28`) and the bare `open('README.md')` (`setup.py:38`). Note `nocodb/` builds
from `setup.py`, not a `pyproject.toml`, so the nocobot pattern may need adapting — if `uv` cannot
lock a `setup.py` project directly, **escalate rather than converting the packaging system
unilaterally.**

Also consider adding `nocodb/.dockerignore` (none exists; `COPY . .` currently sweeps in `docs/` —
including the 2.9 MB of vendored FastMCP docs — plus `*.egg-info` and `.pytest_cache/`, busting the
layer cache on every docs edit).

### 5. Turn camelCase warnings into hard errors in tests

Report §3.4: set `mcp_camelcase_compat` / `FASTMCP_MCP_CAMELCASE_COMPAT=False` in the test config so
any surviving camelCase read raises `AttributeError` instead of warning. This is how you prove the
migration is complete rather than merely quiet.

### 6. Residual checks

- `grep -rn '\.ping(' nocodb/ nocobot/` — `client.ping()` **raises on the modern protocol era**
  (report §3.5). Expected zero hits; confirm.
- `mcpserver/__init__.py:7-8` advertises `fastmcp run nocodb.mcpserver.server:mcp` and `fastmcp dev`
  — verify both still work.
- Report §3.4: resource-not-found error code changed `-32002` → `-32602`. Check nothing asserts on
  the old code.

---

## Explicitly OUT of scope

- `require_confirm` dead code (report §4.7) — report it, do not fix it
- The `/mcp` mount path hardcoding (report §4.6) — **report it with a recommendation**; making it
  explicit is tempting but it is a behaviour change and belongs in its own commit
- The Tool Search transform (report §3.5) — genuinely attractive at 60 tools, but it is a feature,
  not a migration step. Recommend it; do not implement it.
- `DEPLOY_MCP.md` build-path contradiction (report §2.4) — flag it
- CI workflows — flag to the architect

---

## Definition of done

- [ ] `fastmcp` 4.x installed; all Phase 1 tests (T1–T6) **green on 4.x**, T5 especially
- [ ] `nocobot` camelCase fixed; the `:103` silent fallback **deleted**, not repointed
- [ ] `generated.py` regenerated under 4.x; still 63 commands
- [ ] Declared floors raised; upper-bound decision stated
- [ ] `nocodb` lockfile added; Dockerfile uses the `--locked` pattern
- [ ] camelCase compat disabled in tests; suite still green
- [ ] `.ping(`, `-32002`, and residual camelCase greps run and reported
- [ ] Full suite run; counts compared against Phases 0–2
- [ ] Committed (do **not** push)

## Commit

Do not commit `nocodb/docs/fastmcp*.txt`, `.claude/`, or `reddit-post-draft.md`.

```
feat(nocodb)!: migrate to FastMCP 4.x

FastMCP 4 is built on MCP Python SDK v2, which renames every
protocol model field camelCase -> snake_case. The wire format is
unchanged and the architecture is untouched: tools, resources,
lifespan, ResourcesAsTools, custom_route and DebugTokenVerifier
all survive unchanged.

nocobot imports the raw MCP SDK and never imports fastmcp, so the
camelCase compat bridge did not cover it. mcp_client.py:162 would
have raised AttributeError; :103 was worse, silently shipping {}
as every tool's schema to the LLM. That fallback is deleted
rather than repointed.

Adds a lockfile and the uv export --locked Docker pattern so
builds stop resolving against live PyPI, and disables camelCase
compat in tests so residual reads fail loudly.

BREAKING CHANGE: requires fastmcp>=4 and pydantic>=2.12.

Refs: nocodb/docs/upgrade/FASTMCP4-UPGRADE-REPORT.md
```

## If you get stuck

Grep `nocodb/docs/fastmcp-full.txt` (**never read whole**). The migration page is at **32446-32907**
— start there. Then escalate to `nocodb-upgrade-architect`.

Escalate rather than improvising on: any packaging-system conversion (§4), any test assertion you
cannot make pass, and anything that would require an architectural change. Report §3.3 says the
architecture survives — if your evidence contradicts that, **the report is wrong and I need to know
immediately.**
