# FastMCP 3.x → 4.x Upgrade Report

**Status:** Authoritative findings document. All four phase agents MUST read this in full before acting.
**Written:** 2026-09-17
**Baseline tag:** `pre-fastmcp4` (commit `d7a5726`) — rollback target for every phase.
**Architect session:** `nocodb-upgrade-architect`

---

## 0. How to use this document

You are one of four phase agents (`nocodb-phase-0` … `nocodb-phase-3`). Read this report, then read
your own phase prompt in `nocodb/docs/upgrade/phase-N.md`. **Do only your phase.** Do not start the
next phase. Commit when your phase is complete and verified.

If you hit anything unclear, missing, or contradictory:

1. **First** consult the FastMCP docs on disk (see §1).
2. **Then** escalate to the architect (`nocodb-upgrade-architect`) via SendMessage. Do not guess,
   do not invent an alternative approach, do not silently work around a blocker.

This repo's global rule is **Fail Fast**: never create a silent fallback that masks a failure.
Report the exact error and stop. That rule is load-bearing for this upgrade — see §4.2.

---

## 1. Reference material on disk

Fetched 2026-09-17, byte-verified against the llmshub registry.

| File | Size | Use |
|---|---|---|
| `nocodb/docs/fastmcp.txt` | 63 KB | Index of every doc page. Safe to read whole. |
| `nocodb/docs/fastmcp-full.txt` | 2.8 MB, 1276 sections | **GREP ONLY — never read whole.** ~721k tokens. |

Key line ranges already located in `fastmcp-full.txt`:

| Topic | Lines |
|---|---|
| **"Upgrading from FastMCP 3"** (authoritative migration page) | 32446–32907 |
| "What's New in FastMCP 4" | 7801–8038 |
| Changelog (v4.0.0 2026-08-31 → v4.0.4 2026-09-15; last 3.x = v3.4.7) | 25536–30335 |
| FAQ / protocol eras | 38776–38914 |
| `ResourcesAsTools` reference | 24019–24123 |
| `DebugTokenVerifier` reference | 13281–13337, 47757–47776 |
| HTTP transport / `custom_route` / `http_app` | ~5047–5500 |
| Lifespan | 16294–16437 |

The corpus is the FastMCP **4** docs site and contains a `/v3/` mirror of the v3 docs, so both
versions are greppable from the same file.

> **STALENESS WARNING (added post-Phase-0).** The corpus was fetched 2026-09-17 and its changelog
> stops at **4.0.4**. PyPI now serves **4.0.5**. Phase 3 will therefore install a release one patch
> ahead of the vendored docs. Probably immaterial for a patch bump — but **Phase 3 must check the
> 4.0.4 → 4.0.5 delta upstream rather than assuming the on-disk corpus is complete.** Do not treat
> this file as the last word on the installed version.

---

## 2. Baseline state (verified 2026-09-17)

### 2.1 Installed vs declared

```
Python 3.13.1 (local venv)   |   Dockerfile builds on python:3.12-slim
fastmcp==3.0.0               |   declared fastmcp>=3.0.2  -> INSTALLED IS BELOW THE FLOOR
mcp==1.26.0                  |   undeclared (transitive via fastmcp)
cyclopts==5.0.0a4            |   undeclared, PRE-RELEASE ALPHA
pydantic==2.12.5             starlette==0.52.1      httpx==0.28.1
requests==2.32.5             litellm==1.81.13       python-telegram-bot==22.6
nocodb==3.0.0 (dist metadata)|   nocodb/__init__.py declares __version__ = "3.1.0"
```

Additional drift: the editable-install finder `__editable___nocodb_3_0_0_finder.py` points at
`/Users/stevegoldberg/Code/Utils/nocodb/nocodb`, **a path that no longer exists** (repo moved to
`Code/_utils/`). Imports currently resolve only because pytest puts rootdir on `sys.path`.

### 2.2 Version pins — every specifier is open-ended

`nocodb/setup.py`:
- `:40-42` `requests>=2.0` (unbounded)
- `:44-49` extra `cli` → `fastmcp>=3.0.2`, `tomli>=2.0.0;python_version<'3.11'`
- `:50-52` extra `mcp` → `fastmcp>=3.0.2`
- `:53-56` extra `all` → `fastmcp>=3.0.2`, `tomli...`

**`fastmcp>=3.0.2` appears at lines 47, 51, 54. No `<4` guard exists anywhere in the repo.**
`cyclopts` and `mcp` are transitive-only — imported directly by `nocodb/cli/generated.py:12-17`
with zero declared constraint.

### 2.3 Lockfiles

| Path | Covers | Contains fastmcp? |
|---|---|---|
| `nocobot/uv.lock` (79 pkgs, uv v1) | nocobot only | **No** — pins `mcp==1.26.0` |
| `nocodb/setup.py` | nocodb | **No lock exists at all** |

There is no `requirements*.txt`, no `poetry.lock`, no constraints file under `nocodb/`.
**The MCP server has zero reproducible-build story.**

Known-good reference pattern to copy — `nocobot/Dockerfile`:
- `:1` `FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
- `:6-7` `COPY pyproject.toml LICENSE uv.lock ./` then `RUN uv export --locked --no-dev --no-hashes > /tmp/requirements.txt`
- `:17-18` `uv pip install --system --no-cache -r /tmp/requirements.txt` then `uv pip install --system --no-cache --no-deps .`

`--locked` fails the build if the lock drifts from the manifest; `--no-deps` on the final install
stops the resolver re-widening. `nocodb/Dockerfile` has none of these three properties.

### 2.4 Deployment exposure

`nocodb/Dockerfile`:
- `:1` `FROM python:3.12-slim` (floating tag, no digest)
- `:6` `RUN pip install --upgrade pip && pip install uv` (**uv itself unpinned**)
- `:9` `COPY . .` (context = `nocodb/`)
- `:10` `RUN uv pip install --system -e ".[mcp]"` ← **resolves against live PyPI every build**
- `:19` `CMD ["python", "-m", "nocodb.mcpserver", "--http"]`

No `nocodb/.dockerignore` exists (only `nocobot/` has one), so `COPY . .` sweeps in `docs/`,
`skills/`, `*.egg-info`, `.pytest_cache/` — a docs-only edit busts the layer cache and forces a
full dependency re-resolve.

`DEPLOY_MCP.md:200-204` documents **Auto Deploy on push**. Combined with the unpinned Dockerfile:
**a README edit can ship FastMCP 4.x to production.** This is the single most urgent fact in this
document and is why Phase 0 exists.

Contradiction to be aware of: `DEPLOY_MCP.md:31,45` says Build Path `/` + Docker Context Path
`nocodb`; `CLAUDE.md:13` says Build Path `/nocodb/`. The Dockerfile only works with context =
`nocodb/` (required by the `package_dir` mapping at `setup.py:20-28` and the bare
`open('README.md')` at `setup.py:38`).

### 2.5 Test coverage — the upgrade has no safety net

209 tests collected (`venv/bin/python -m pytest --collect-only -q`), **no configfile detected**,
no `conftest.py` anywhere in the repo.

| File | Tests | Layer |
|---|---|---|
| `nocodb/infra/requests_client_test.py` | 78 | HTTP client (mocks `requests`) |
| `tests/test_integration_full.py` | 57 | Live SDK E2E |
| `nocodb/filters/filters_test.py` | 30 | Filters |
| `nocobot/channels/telegram_test.py` | 15 | Bot channel |
| `nocodb/filters/logical_test.py` | 10 | Filters |
| `nocobot/agent_test.py` | 10 | Bot agent |
| `nocodb/filters/factory_test.py` | 5 | Filters |
| `nocobot/providers/retry_test.py` | 4 | Bot provider |

**Zero tests import `fastmcp`, `FastMCP`, `mcpserver`, or any of the 16 tool modules.** Grep
confirms no hits. Nothing exercises `ResourcesAsTools`, `DebugTokenVerifier`, `custom_route`, or
`mcp.run()`.

**Worse: the 57 integration tests never run.** `tests/test_integration_full.py:39-42` skips the
module unless `NOCODB_URL` **and** `NOCODB_API_KEY` are set. The repo `.env` defines `NOCODB_URL`,
`NOCODB_TOKEN`, `NOCODB_BASE_ID`, `NOCODB_VERIFY_SSL` — **`NOCODB_API_KEY` does not exist in it**.
The skipif evaluates True. Effective offline coverage: **152 tests, 0 of them MCP**.

Secondary: `tests/test_integration_full.py:21` imports `dotenv`, declared nowhere.
`nocobot/pyproject.toml:55-56` sets `asyncio_mode = "auto"` but pytest reports no configfile from
repo root, so it is not applied.

### 2.6 CI

`.github/` contains **only** templates (`PULL_REQUEST_TEMPLATE.md`, `ISSUE_TEMPLATE/bug.md`,
`ISSUE_TEMPLATE/feature.md`). **No `.github/workflows/` exists.** No dependabot, no renovate, no
pre-commit. Nothing runs tests on push, PR, or schedule.

The scheduled-rebuild risk is therefore not in CI — it is in Dokploy auto-deploy (§2.4).

---

## 3. FastMCP 4 — what actually changed

Root cause of nearly every break: **FastMCP 4 is built on MCP Python SDK v2**, which moved protocol
types to a standalone `mcp_types` package and renamed every model field camelCase → snake_case
(`inputSchema` → `input_schema`, `isError` → `is_error`). **The wire format is unchanged**
(`fastmcp-full.txt:32451`).

### 3.1 Breaking changes RELEVANT to this repo

| # | Change | Impact here | Cite |
|---|---|---|---|
| B1 | camelCase → snake_case on all protocol models | **8 read sites** — see §4 | 32446+, 32557-32580 |
| B2 | `pydantic>=2.12` is the new floor | venv already at 2.12.5 → OK; must raise declared floor | 32545-32551 |
| B3 | `starlette>=1.0.1` floor (server extra) | **CORRECTED:** this already happened *under the 3.x cap*. Phase 1's upgrade to fastmcp 3.4.7 pulled starlette 0.52.1 → **1.6.0**. Not a 4.x-only floor. | 32545-32551 |
| B4 | FastAPI must be ≥0.133.0 to admit Starlette 1.x | **N/A — repo does not use FastAPI** | 32545-32551 |
| B5 | httpx → httpx2 wholesale | **N/A** — `except httpx.` grep = 0 hits | 32641-32678 |

### 3.2 Breaking changes NOT applicable — verified zero hits

A repo-wide grep for every removed/changed API returned **zero hits** for all of:

`ctx.sample`, `ctx.sample_step`, `ctx.list_roots`, `ctx.elicit`, `ctx.set_state`,
`sampling_handler`, `import_server`, `as_proxy`, `serializer=`, `exclude_args=`, `McpError(`,
`ErrorData(`, `except httpx`, `httpx_client_factory`, `decorator_mode`, `FASTMCP_DECORATOR_MODE`,
`sse_read_timeout`, `task=True`, `add_tool_transformation`, `remove_tool_transformation`,
`remove_tool(`, `on_initialize`, `SkillsProvider`, `CachableToolResult`, `TaskConfig`,
`PromptToolMiddleware`, `ResourceToolMiddleware`, and every moved module path.

No `@mcp.prompt` is used. No `Context`/`ctx` injection is used anywhere. No middleware is used.
Nothing reads attributes off a decorated tool result.

**Do not spend time on these.** They are confirmed non-issues.

### 3.3 Everything structural SURVIVES 4.x

Confirmed still valid in the v4 docs — **no change required**:

| API | Used at | v4 status |
|---|---|---|
| `@mcp.tool`, `@mcp.tool(annotations={...})` | 60 sites | Unchanged (32737, 34245) |
| `@mcp.resource(uri=, name=, description=, mime_type=)` | `resources/__init__.py:27,38,49` | Unchanged |
| `@asynccontextmanager` lifespan → `FastMCP(lifespan=...)` | `server.py:20-35,50-54` | **Explicitly still supported** (16380-16393) |
| `ResourcesAsTools` + `mcp.add_transform(...)` | `server.py:13,57` | Unchanged; now the *recommended* path (24019-24123). **Generates exactly 2 tools** (`list_resources`, `read_resource`), not one per resource — see §4.3 correction |
| `@mcp.custom_route("/health", methods=["GET"])` | `server.py:63-66` | Still the documented health-check pattern (~5244) |
| `mcp.run(transport="http", host=, port=)` | `__main__.py:58` | Unchanged (~5080); `path=` still supported (~5123) |
| `DebugTokenVerifier(validate=, client_id=)` | `server.py:12,41-44` | **Still exists, same signature** (13281-13337, 47757-47776) |
| `ToolError` from `fastmcp.exceptions` | `errors.py:6` + 18 inline | Unchanged |

**The migration is NOT architectural.** It is the 8 camelCase reads plus dependency floors.

### 3.4 Deprecated-but-working (warns; removal scheduled)

- **camelCase reads are bridged** with `FastMCPDeprecationWarning`, controlled by
  `mcp_camelcase_compat` / env `FASTMCP_MCP_CAMELCASE_COMPAT`. Set `False` in tests to turn them
  into hard `AttributeError` (32557-32580, 32850-32852).
- **CRITICAL SCOPE LIMIT:** the bridge covers only "objects FastMCP hands back to you" —
  `client.list_tools()`, `call_tool_mcp()`, `read_resource()`, sampling/elicitation handler params.
  **It does NOT cover raw MCP SDK objects obtained without FastMCP.** This is exactly why `nocobot`
  breaks hard and `cli/generated.py` only warns (§4.1 vs §4.2).
- `Client("server.py")` bare-string stdio inference → warns, removed in FastMCP 5 (32829-32836).
- `ctx.info` emits an SDK deprecation warning (benign, delivery unaffected) (32854-32862).

### 3.5 New in 4.x worth knowing (not required by any phase)

- **Tool Search transform** (`fastmcp.server.transforms.search`, bm25/regex) — replaces the full
  catalog with on-demand search. Directly relevant at 60 tools (24126-24133).
- Dual-era protocol from one deployment; modern era is **stateless** → no session affinity needed
  behind a load balancer (7816-7838).
- Server-level cache hints `FastMCP("X", cache_ttl=300, cache_scope="public")` (8014-8022).
- `client.ping()` **raises on the modern era** (`Method not found`); pin `mode="legacy"` if any
  health check depends on it (32817-32848). ← **Phase 3 must grep for `.ping(`.**

---

## 4. The actual defects to fix

### 4.1 `nocobot` — HARD BREAK, no compat bridge

`nocobot` imports **only the raw MCP SDK** (`nocobot/mcp_client.py:10-12`:
`from mcp import ClientSession`, `mcp.client.streamable_http.streamablehttp_client`) and
**never imports fastmcp**. Per the documented scope limit (§3.4), the camelCase bridge does not
apply. Empirically verified against an SDK-v2 install:

```
Tool fields:           [... 'input_schema' ...]        # 'inputSchema' absent
CallToolResult fields: [... 'structured_content', 'is_error' ...]
hasattr(Tool, 'inputSchema') -> False
```

| Site | Current code | Failure mode |
|---|---|---|
| `nocobot/mcp_client.py:162` | `result.isError` | **Hard `AttributeError`** — loud, acceptable |
| `nocobot/mcp_client.py:103` | `tool.inputSchema if hasattr(tool, 'inputSchema') else {}` | **SILENT** — guard goes False, ships `{}` as every tool's parameter schema to the LLM |

**Line 103 is the most dangerous defect in this repo.** It does not crash. It degrades the agent to
schema-less tools, so the LLM starts guessing at parameters, and the symptom surfaces days later as
"the bot got worse" with no error trail. It is a silent fallback masking a hard failure — a direct
violation of the Fail Fast rule in `~/.claude/CLAUDE.md`.

**The fix is NOT to repoint the guard at `input_schema`.** Delete the fallback. If a tool has no
schema, that is an error worth raising, not a `{}` worth shipping.

**Mitigating factor:** `nocobot/uv.lock` pins `mcp==1.26.0` and `nocobot/Dockerfile` uses
`uv export --locked`, so nocobot is protected **today**. These two bugs are latent until someone
runs `uv lock --upgrade`. They are not urgent, but they are certain.

### 4.2 `nocodb/cli/generated.py` — bridged, warns only

This file **does** `from fastmcp import Client` (`:16`), so its camelCase reads are bridged.

Sites: `:56` `block.mimeType`, `:59`, `:91-92` `tool.inputSchema`, `:133`, `:177`
`msg.content.mimeType`.

**UNVERIFIED:** the bridge could not be confirmed at runtime. The user-site fastmcp 4.0.3 install is
broken (`from fastmcp import Client` → `ImportError: ... unknown location`), matching the documented
pip-upgrade issue whose fix is `pip install --force-reinstall fastmcp` (38896-38898). Phase 3 must
verify the bridge empirically rather than trusting this.

### 4.3 `nocodb/cli/generated.py` is STALE — pre-existing, blocks clean signal

> **CORRECTED 2026-09-17 after Phase 1 challenged this section.** The original text claimed the
> server exposes 63 tools (60 + "3 `ResourcesAsTools`-derived"). **That was wrong.**
> `ResourcesAsTools` generates exactly **two** tools — `list_resources` and `read_resource` —
> regardless of how many resources exist. The 3 resources are reached *through* `read_resource`,
> not exposed as 3 separate tools. Confirmed three ways: the installed 3.4.7 class docstring
> ("Generates two tools:"), `fastmcp-full.txt:23899`, and a live in-memory client count.
> **The correct total is 62 = 60 `@mcp.tool` + 2 transform-derived.**

**The counts match. The name sets do not.** Measured live by the architect against `generated.py`:

```
generated.py commands: 62
live server tools    : 62

GHOSTS  (in CLI, not on server): ['get_reference', 'get_workflow_guide']
MISSING (on server, not in CLI): ['list_resources', 'read_resource']
```

**This is a trap.** A count-based check (`62 == 62`) passes while the CLI is genuinely broken: it
exposes two dead commands pointing at a deleted module, and is missing the two commands that reach
the 3 resources at all. **Phase 2 must compare name sets, never counts.** Any check that asserts a
number here will report success on a broken artifact.

- The two ghosts are `get_workflow_guide` (`:1558`) and `get_reference` (`:1580`), from
  `nocodb/mcpserver/tools/docs.py` — **a module that has been deleted**.
- The two missing are the `ResourcesAsTools` pair, absent because the CLI predates that switch.
- Last regenerated at `c13aa72` (2026-03-11). The `ResourcesAsTools` switch (`09ddf0a`) and the
  formula-resource change (`327954e`) both landed 2026-03-12 **without a regen**.
- `nocodb/docs/CLI.md:3` still documents "62 commands".

**This must be reconciled on 3.x BEFORE the 4.x bump.** Otherwise upgrade breakage is
indistinguishable from drift that already existed.

### 4.4 `regenerate-cli.sh` fails open

`nocodb/scripts/regenerate-cli.sh` post-processes generated source with regex surgery (`:62-97`),
matching literal strings like `app = cyclopts.App(name="localhost", help="CLI for localhost MCP server")`.

**It prints "Updated CLIENT_SPEC, app name, docstring" and exits 0 whether or not any regex
matched.** A 4.x generator emitting a different template makes every substitution a silent no-op
and the script still reports success. This must be hardened to fail loudly on a non-match.

Pipeline for reference (`regenerate-cli.sh`):
1. `:17-26` source `.env`, pick free port from 9876
2. `:29` launch `python3 -m nocodb.mcpserver --http --port $PORT &`, sleep 3
3. `:39` `fastmcp generate-cli "http://localhost:$PORT/mcp" ... -f --timeout 60` ← only FastMCP dep
4. `:47` kill server; `:50-103` Python regex post-process
5. `:106-112` `sed` fixups targeting `cli/SKILL.md` — **but the actual file is `nocodb/cli/skill.md`**
   (case mismatch; another silent no-op)
6. `:115-125` count commands and print total

### 4.5 `DebugTokenVerifier` permissive default — standing hazard, NOT an upgrade break

Verified by direct inspection of the installed 3.0.0 class:

```
DebugTokenVerifier.__init__(self,
    validate: 'Callable[[str], bool] | Callable[[str], Awaitable[bool]]' = <lambda>,
    client_id: 'str' = 'debug-client', scopes=None, required_scopes=None)

Docstring: "By default, it accepts all non-empty tokens (useful for testing)."
           "WARNING: This bypasses standard..."
```

`server.py:40-47` passes `validate=lambda token: hmac.compare_digest(token, _api_key)`. If that
kwarg were ever dropped, renamed, or swallowed, the server would construct successfully with the
**accept-everything** default, `/health` would still return `{"status":"ok"}` (it is a static
handler that never touches auth — `server.py:63-66`), Dokploy would go green, and `/mcp` would
accept any bearer token.

**This does NOT fire on the 4.x upgrade** — the class and signature survive (§3.3). But the
structural hazard is real and permanent. **Phase 1 must add a test asserting auth REJECTS a wrong
token**, which is the only thing that would ever catch this class of regression.

Related: auth is read at **import time** (`server.py:39` `os.environ.get("MCP_API_KEY")`) and applied
unconditionally, including in stdio mode.

### 4.6 `/mcp` mount path is assumed, never configured

`mcp.run()` never passes `path=`. The `/mcp` path is FastMCP's default, but it is hardcoded
downstream in `nocodb/scripts/regenerate-cli.sh:39` and `nocobot/config.py:20`. A default change
breaks the bot and CLI regeneration silently while the server itself looks healthy.

### 4.7 Dead code

`require_confirm` is defined at `nocodb/mcpserver/errors.py:43-66` and **never applied to any tool**
(referenced only in its own docstring at `:50`). Every destructive tool instead does an inline
`confirm` check plus an inline `ToolError` import (e.g. `tools/records.py:235-240`).

---

## 5. Architecture facts phase agents need

### 5.1 Tool registration is import-side-effect based

No `register(mcp)` function, no dynamic loop. Each of the 16 modules does `from ..server import mcp`
and decorates module-level functions. `server.py:75-92` imports all 16 modules **at the bottom of
the file** (with `# noqa: E402, F401`), then `from . import resources` at `:95`.

This is a **deliberate circular import** (`server` → `tools.x` → `server`) that works only because
the imports sit after `mcp` is constructed at `server.py:50`. **Do not reorder these imports.**

Per-module tool counts (total 60): records 7, fields 6, view_filters 6, webhooks 6, tables 5,
view_sorts 5, members 4, shared_views 4, view_columns 4, links 3, views 3, bases 2, schema 2,
attachments 1, export 1, storage 1.

Decorator order is always `@mcp.tool` outermost, `@wrap_api_error` inner
(`errors.py:14`, 60 occurrences).

Resources: 3, registered the same way in `resources/__init__.py:27,38,49`, markdown read from disk at
import time (`:17-19`), shipped via `package_data` (`setup.py:29`).

### 5.2 Structured output is implicit

Tools return plain `@dataclass` return annotations (43 dataclasses in `mcpserver/models.py:1-364`).
FastMCP derives output schemas from them. No pydantic models, no `Annotated`/`Field`, no
`output_schema=`, no `tags=`/`meta=`/`enabled=`.

### 5.3 Transports

`nocodb/mcpserver/__main__.py:52-61`:
```python
run_kwargs = {}
if args.reload:
    run_kwargs["reload"] = True
if args.http:
    mcp.run(transport="http", host=args.host, port=args.port, **run_kwargs)
else:
    mcp.run(**run_kwargs)
```
stdio relies on the **default** transport (no `transport=` passed). Host default `0.0.0.0`/`MCP_HOST`
(`:39-43`), port default `8000`/`MCP_PORT` (`:33-38`).

`mcpserver/__init__.py:7-8` advertises `fastmcp run nocodb.mcpserver.server:mcp` and
`fastmcp dev ...` in its docstring — verify these still work post-upgrade.

---

## 6. Phase plan

| Phase | Agent | Goal | Gate |
|---|---|---|---|
| **0** | `nocodb-phase-0` | Cap the pin at `<4`. Stop prod from self-upgrading. | Fresh resolve picks 3.x, not 4.x |
| **1** | `nocodb-phase-1` | Build the MCP test net on 3.x. | Tests import FastMCP, assert 63 tools, assert auth **rejects** |
| **2** | `nocodb-phase-2` | Clear pre-existing drift on 3.x. | `generated.py` = 63 cmds, no ghosts; regen script fails loudly |
| **3** | `nocodb-phase-3` | Migrate to 4.x. | Phase-1 tests green on 4.x; camelCase compat off |
| **4** | architect | Live verification. | Health, auth reject, 63 tools, nocobot E2E |

**Ordering is not negotiable.** Phase 0 before 1 because prod is currently exposed. Phase 2 before 3
because stale `generated.py` poisons the upgrade signal. Phase 1 before 3 because there is otherwise
nothing to detect a regression with.

### 6.1 Scope amendment after Phase 0 (2026-09-17)

Phase 0 (commit `40dd089`) proved the cap binds: `fastmcp>=3.0.2,<4` resolves to **3.4.7**, uncapped
resolves to **4.0.5**. Independently re-verified by the architect.

That surfaced a gap the original plan missed. **The local venv has `fastmcp==3.0.0`, but a prod
rebuild under the cap now installs `3.4.7`** — a four-minor jump. Building the Phase 1 test net on
3.0.0 would mean testing against a version nobody runs, which reproduces the exact defect this
report criticises in §2.1: *the environment you test in and the environment that ships share no
dependency resolution*.

**Decision: environment normalisation moves from Phase 2 into Phase 1, as its step 0.**

- Phase 1 upgrades the venv to the version the cap resolves to (3.4.7) **before** writing any test,
  and repairs the dead editable-install finder (§2.1).
- Phase 1 then raises the declared floor to `fastmcp>=3.4.7,<4` so the declared floor equals the
  tested version. This removes the 4-minor unknown entirely rather than carrying it into Phase 3.
- Phase 2 no longer owns the venv/editable repair. Its §4 item is struck.

Rationale: a test net is only worth what its environment fidelity is worth. Normalising first costs
minutes; discovering in Phase 3 that the tests were written against 3.0.0 behaviour costs the whole
upgrade's attribution.

### 6.2 Amendments after Phase 1 step 0 (2026-09-17)

Phase 1 challenged §4.3 and was right. Three corrections, all architect-verified:

**(a) Tool count is 62, not 63.** See the §4.3 correction block. `ResourcesAsTools` makes 2 tools,
not 3. T1 in `phase-1.md` was wrong and is amended. **Phase 1's proposed fix is approved and
preferred:** assert the *structure* — 60 tool-derived names plus exactly
`{list_resources, read_resource}` — rather than a magic number, so the test names what drifted
instead of just failing an integer comparison. Given that a `62 == 62` count check passes on a
demonstrably broken CLI (§4.3), magic-number assertions are actively harmful here.

**(b) The `import fastmcp` ImportError is a 3.x problem too.** §4.2 attributed
`cannot import name 'FastMCP' from 'fastmcp' (unknown location)` to a broken user-site 4.0.3
install. It actually hits **any** pip upgrade from ≤3.2 to ≥3.3 (`fastmcp-full.txt:38896`). Phase 1
hit it going 3.0.0 → 3.4.7. Fix is `pip install --force-reinstall fastmcp`. **Phase 3 will hit this
again on the 4.x bump — expect it, do not treat it as a migration failure.**

**(c) The dependency cascade from `--force-reinstall` is accepted, not reverted.** It moved:

| Package | Before | After |
|---|---|---|
| mcp | 1.26.0 | 1.30.0 |
| pydantic | 2.12.5 | 2.13.5 |
| pydantic-settings | 2.12.0 | 2.15.0 |
| cyclopts | **5.0.0a4** (pre-release) | **4.25.3** (stable) |
| starlette | 0.52.1 | 1.6.0 |

Accepted because surgically pinning packages back would build a hybrid environment nobody ships —
the same test-env/ship-env divergence §6.1 exists to eliminate. Two upsides: cyclopts moves off the
undeclared pre-release alpha flagged in §2.2 onto what a fresh resolve actually picks, and pydantic
now clears the 2.12 floor B2 requires.

**One consequence Phase 3 must carry:** the venv's `mcp` (1.30.0) now diverges from
`nocobot/uv.lock`'s pinned **1.26.0**. Both are SDK **v1** (camelCase), so §4.1's analysis stands
unchanged — but when Phase 3 fixes the nocobot camelCase reads, it will be testing against 1.30.0
while nocobot's Docker build ships 1.26.0. Refresh that lock as part of Phase 3 rather than leaving
the divergence.

**(d) Baseline unchanged.** 152 passed / 57 skipped, identical to Phase 0. The warning count reads 4
instead of 3; Phase 1 traced it to a pre-existing leaked coroutine in `nocobot/agent_test.py` being
GC'd during an unrelated test, so pytest attributes it to a 4th test name. Same defect, same source
— only the label moved. Not a regression.

### 6.3 Out-of-scope finding: nocobot's editable install is broken

Reported by Phase 1, **not fixed, not assigned**. `nocobot/pyproject.toml` sets
`packages = ["nocobot"]`, but the pyproject sits *inside* the package directory, so hatchling
resolves it to `nocobot/nocobot`, which does not exist. The old `_nocobot.pth` was 0 bytes. Local
`import nocobot` resolves only because pytest puts rootdir on `sys.path` — the same luck as the
nocodb finder in §2.1.

**Production is unaffected:** `nocobot/Dockerfile:9-14` reconstructs the hierarchy at COPY time
deliberately. This is a local-dev-only defect. It touches packaging, so it is explicitly **not**
folded into Phase 3 — flagged for a separate decision.

---

## 7. Rules for every phase agent

1. **Read this report fully before acting.** Read your phase prompt second.
2. **Your phase only.** Do not drift into another phase's scope. If you spot something outside your
   phase, report it to the architect — do not fix it.
3. **Fail Fast.** No silent fallbacks, no alternative approaches without consent. Exact error, stop.
4. **Read before editing.** Never assume file contents. Verify APIs with grep before using them.
5. **Docs first, then escalate.** Grep `nocodb/docs/fastmcp-full.txt` (never read whole). If the
   answer is not there, escalate to `nocodb-upgrade-architect`.
6. **Run the tests.** Do not report done on unverified work.
7. **Commit when complete**, scoped to your phase. Do not push. Do not commit
   `nocodb/docs/fastmcp*.txt` (2.9 MB of vendored upstream docs — gitignored), `.claude/`, or
   `reddit-post-draft.md`.
8. **Report honestly.** If something is blocked or partially done, say so explicitly.

Rollback at any point: `git reset --hard pre-fastmcp4`.
