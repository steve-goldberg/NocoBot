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
| `nocodb/docs/mcp-sdk.txt` | 4.8 KB | MCP **Python SDK** index (distinct from FastMCP). Safe to read whole. |
| `nocodb/docs/mcp-sdk-full.txt` | 776 KB, 14370 lines | **GREP ONLY.** Raw SDK docs — v1→v2 transport recipe at `3479-3527`, error lookup at `1440-1458`. |

The two `mcp-sdk*` files were added 2026-09-17 from `https://py.sdk.modelcontextprotocol.io/llms.txt`
after the nocobot finding (§6.6) showed the FastMCP corpus cannot answer raw-SDK questions. All four
files are gitignored.

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
| **1** | `nocodb-phase-1` | Build the MCP test net on 3.x. | ✅ `d047b6d` — 12 tests, auth **rejects** proven by mutation |
| **2** | `nocodb-phase-2` | Clear pre-existing drift on 3.x. | ✅ `92d495c` — name sets match; regen script fails loudly |
| **3** | `nocodb-phase-3` | Migrate to 4.x. | ✅ `f48d507` — 13 tests green on 4.0.5, compat off |
| **3b** | `nocodb-mcp-v2-protocol-upgrade` | nocobot → `fastmcp.Client`. | ✅ `bad76bf` — auth gate proven by mutation |
| **4** | architect | Live verification. | ✅ **PASSED** — see §7 |

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

### 6.4 Phase 1 complete (`d047b6d`) — and a live-credential hazard every later phase must respect

12 tests in `nocodb/mcpserver/mcpserver_test.py`, plus `pytest.ini` and `conftest.py`. Suite:
**164 passed / 57 skipped**. Architect-verified: suite re-run independently, `server.py` confirmed
byte-identical to `pre-fastmcp4`, and the **T5 mutation independently reproduced** — removing
`validate=` from `server.py:41-44` fails exactly one test, T5, while `/health` stays green and the
correct-token test still passes. The net can fail on the real defect.

#### ⚠️ INCIDENT — the live integration suite was run against the real NocoDB instance

During Phase 1, a verification command using `env -u NOCODB_URL -u NOCODB_TOKEN` **did not suppress
the credentials**, because `tests/test_integration_full.py:22` calls `load_dotenv()` on the repo
`.env` and repopulated them. The 57 destructive integration tests — which create and delete a real
base — executed against the user's live instance.

Reported outcome: teardown cleaned up, no `SDK_Integration_Test_Base` remains, and the only failures
were the v2 view/webhook creates that `CLAUDE.md` already documents as broken in self-hosted.

**The rule this establishes, binding on Phases 2–4:**

> `tests/test_integration_full.py` self-loads the repo `.env`. **`env -u VAR` does not make it
> safe.** Unsetting an environment variable cannot protect you from a module that reads the
> credentials off disk itself. The only safe gate is the explicit opt-in flag.

Phase 1's mitigation: the suite now requires `NOCODB_RUN_INTEGRATION=1`, and requesting it without
credentials raises `RuntimeError` at import rather than skipping silently. Architect-verified: with
the flag unset, all 57 skip rather than execute.

This also retroactively justifies the fix. Correcting the `NOCODB_API_KEY` → `NOCODB_TOKEN` name
alone — the obvious reading of the original Phase 1 brief — **would have switched 57 destructive
tests ON by default for anyone running plain `pytest` at the repo root**, because the module
supplies its own credentials. The opt-in flag is load-bearing, not ceremony.

**Any phase that runs a command touching `.env` is touching production.** That includes
`regenerate-cli.sh`, which sources `.env` and boots the real server (Phase 2).

#### Test-harness portability — Phase 3 must not misread this

The new tests import **`httpx`** directly for `ASGITransport` (auth cannot be tested through the
in-memory client, which bypasses HTTP middleware; T4–T6 go through `mcp.http_app()`).

**This narrows §3.1 B5.** B5 marked the httpx→httpx2 move N/A on the grounds that `except httpx.`
had zero hits. That was true of application code and is still true — but the *test harness* now
depends on plain `httpx` being importable. If 4.x drops it from the dependency tree, **T4–T6 fail at
import. That is a harness break, not a migration defect, and must not be reported as one.**

Port target: FastMCP 4 ships `fastmcp.utilities.tests` (`asgi_server`, `asgi_client`, `http_client`),
which does not exist in 3.4.7 — verified by Phase 1, which is why it was not used.

Two further notes from Phase 1 for Phase 3:

- **T1 and T3 are deliberately strict.** T3 pins the zero-argument tool set to exactly
  `{bases_list, base_info, tables_list, members_list, schema_export_base, list_resources}` — those
  six are genuinely zero-arg (they operate on the configured base), so a blanket "properties must be
  non-empty" would have been wrong. If 4.x changes how `ResourcesAsTools` names or schemas its two
  tools, T1/T3 fail **by design**. Read such a failure as "the transform changed", not "the server
  broke".
- **The integration-test fix is NOT committed.** `tests/` is gitignored (`.gitignore:15`), so the
  `NOCODB_RUN_INTEGRATION` guard lives only in the local working copy and will not survive a fresh
  clone. Phase 1's recommendation: keep `tests/` ignored (the files may carry real NocoDB details,
  and history would retain them), and decide separately between (a) leaving it as a documented
  local-only harness, or (b) moving credential-free parts into tracked colocated `*_test.py` files
  and keeping only live E2E under `tests/`. **Unresolved — user's call.**

Also added in Phase 1: a `test` extra in `setup.py` (pytest, pytest-asyncio, python-dotenv, fastmcp,
httpx), deliberately **not** folded into `all`, so test dependencies never reach the Docker image
(which installs `.[mcp]`).

### 6.5 Phase 2 complete (`92d495c`) — four more report corrections

Name sets now match exactly (architect-verified: `GHOSTS: []`, `MISSING: []`, suite 164/57).
`regenerate-cli.sh` now asserts all five source substitutions plus four skill-file fixups, and
writes nothing if any fails — proven by deliberately breaking a pattern (exit 1).

**Correction A — §4.4 item 5 was wrong.** The `sed` block targeting `cli/SKILL.md` was *not* a
silent no-op. macOS APFS is case-insensitive: `ls -i` gives `cli/SKILL.md` and `cli/skill.md` the
**same inode (154415357)** — architect-verified. The sed has been running all along. It remains a
latent bug on any case-sensitive filesystem, so hardening was still correct, but the diagnosis was
not. Phase 2 moved all four fixups into the asserted Python block, which also normalises the name
(`generate-cli` writes `SKILL.md`; the tracked file is `skill.md`).

**Correction B — §2.1's `nocodb 3.0.0` was an artifact, not a skew.** `setup.py:16` calls
`get_version()`, which regexes `__version__` out of `__init__.py`, so the two **cannot** disagree.
The stale 3.0.0 came from an orphaned, gitignored `./nocodb.egg-info/` at the **repo root** (dated
Feb 13 2026, no `setup.py` beside it — a pre-monorepo leftover). Repo root is on `sys.path`, so it
shadowed the real dist; from `/tmp` the same venv already reported 3.1.0. Removed (backed up to
`/tmp/nocodb.egg-info.backup-3.0.0`). Architect-verified: now reads **3.1.0** from the repo root.
So "release never cut or bump never installed" was a false dichotomy — neither.

**Correction C — "123 tests" in `CLAUDE.md` was correct.** My `phase-2.md` implied it needed
updating to 209. It does not: that line sits under `### nocodb SDK`, and
`pytest --collect-only nocodb/infra nocodb/filters` returns exactly **123** (78+30+10+5) —
architect-verified. Overwriting it would have *introduced* an error. Clarified instead: 123 SDK,
12 MCP, 221 repo-wide.

**Correction D — new finding in nocobot.** `nocobot/mcp_client.py:218` described
`nocodb://tools-reference` as "All 62 tools"; the resource actually names only **53** of the 62.
Replaced with a count-free description rather than another number that rots. One line in an LLM
prompt string, unrelated to the camelCase sites at `:103`/`:162`.

**Two further fail-open paths found in `regenerate-cli.sh`, beyond the four I listed:**
1. `PROJECT_DIR` was not exported until `:114`, *after* the post-processing heredoc at `:50`, so
   `os.environ.get("PROJECT_DIR","")` was empty and the path fell through to a cwd-relative
   `cli/generated.py`. It only ever worked because the script is run from `nocodb/`.
2. `sed -i ''` is BSD-only and fails on GNU sed.

**Scope addition, approved:** Phase 2 replaced the script's trailing count print with a **name-set
gate against the live server**. The four template assertions catch generator drift, but nothing in
the script would have caught the semantic drift this phase existed to fix. Proven by mutating a
command name to `records_list_TYPO`: count stays 62, exit 1 with both difference lists. **Keep it.**

#### Credential exposure during regeneration: none

Contrary to the §6.4 warning's worst case, the regen sent **zero requests** to the live instance.
`dependencies.py:126-137` `init_dependencies()` only constructs a client object with no network
call (confirmed: it "connects" to `https://example.invalid` instantly and without error), and
`generate-cli` calls only `list_tools`. The access log shows only localhost `/mcp` traffic.
Credentials were present in the process environment but nothing was transmitted. The §6.4 rule
still stands for Phases 3–4 — but running `regenerate-cli.sh` is not itself a data-touching act.

#### ⚠️ Generator template change — Phase 3 must NOT attribute this to 4.x

The **3.4.7** generator already emits a materially different template from 3.0.0. Absorbed by
`92d495c`, but it will look like upgrade damage if encountered cold:

- `cli/skill.md`: **39044 → 28211 bytes** (1522 → 923 lines). 3.0.0 dumped each tool's entire
  docstring; 3.4.7 emits only the summary paragraph. **Lost:** every `Returns:` block and the
  filter-syntax prose on `records_list`.
- **Gained:** the per-flag Description column, previously empty or `"JSON string"`, is now populated
  from real parameter descriptions. `generated.py` makes the same trade — command docstrings shrink,
  `cyclopts.Parameter(help=...)` goes from `""` to real text.
- Cosmetic upstream defect in 3.4.7: parameter help embeds a **literal `\n`** (escaped, not a
  newline) before the inlined JSON Schema blob, so `--help` renders
  `...(e.g., "Name,Email,Status")\nJSON Schema: {...}`. Generated output — do not hand-fix.

**Open item, user's call:** whether the lost `skill.md` prose matters. Mitigating: `docs/FILTERS.md`,
`skills/cli/nocodb-v3-cli-skill.md`, and `mcpserver/resources/tools-reference.md` all still carry
filter syntax. If it does matter, the fix belongs in a post-processing step or companion doc —
**never a hand-edit of generated output.**

### 6.6 ⚠️ §4.1 UNDERSTATED nocobot — it is a full SDK v1→v2 migration

**Found by Phase 3. The most consequential error in this report.** §4.1 called nocobot "2 camelCase
reads". It is a transport-signature break plus a dependency-boundary problem.

Architect-verified against the installed tree (`mcp==2.2.0`, `fastmcp==4.0.5`, `httpx2==2.13.0`):

```
from mcp.client.streamable_http import streamablehttp_client   -> ImportError
from mcp.client.streamable_http import streamable_http_client  -> OK
  signature: ['url', 'http_client', 'terminate_on_close']
```

| | v1 (1.30.0) | v2 (2.2.0) |
|---|---|---|
| name | `streamablehttp_client` | `streamable_http_client` |
| params | `url, headers=, timeout=, sse_read_timeout=, terminate_on_close=, httpx_client_factory=, auth=` | `url, *, http_client: httpx2.AsyncClient\|None, terminate_on_close` |

**`headers=` and `timeout=` are gone.** `nocobot/mcp_client.py:49` passes both, and `headers` is where
the `MCP_API_KEY` bearer lives (`:32`). Under v2 they must be supplied via a constructed
`httpx2.AsyncClient`, making httpx2 a nocobot runtime dependency (it currently declares
`httpx>=0.25.0` at `pyproject.toml:26`). `sse_client` (`:48`) **keeps** `headers=`/`timeout=` — the
two transports now diverge.

**Why the report missed it:** §3.2 grepped for removed *FastMCP* APIs. nocobot imports none — it
imports the raw SDK, and the raw SDK's client surface moved too. The grep was scoped to the wrong
library for that service.

**Why it blocked the camelCase fix:** Phase 3 inspected the mcp 1.30.0 wheel directly —
`types.py:1320` `inputSchema`, `:1369` `isError`, no `populate_by_name`, no `alias_generator`. There
are **no snake_case aliases on v1**. So `result.is_error` raises `AttributeError` on the version
nocobot's Docker actually ships. The camelCase fix and the SDK migration are a package deal.

#### The consequence neither the report nor Phase 3 stated: the shared venv is now unusable

nocodb on FastMCP 4 requires `mcp>=2`; nocobot's code requires `mcp<2`. **One venv can no longer
hold both.** Architect-verified: `import nocobot.mcp_client` raises ImportError, and the repo-root
suite went from 164 passing to `ERROR nocobot/agent_test.py — Interrupted: 1 error during
collection`, i.e. **zero tests run**.

Production was never affected — the two Dockerfiles build independently and nocobot has its own
`uv.lock`. Only local dev shared an environment.

#### DECISION (user, 2026-09-17): migrate nocobot to SDK v2 now

Phase 3 recommended cap-and-defer (`mcp<2`, refresh lock within v1, delete the `:103` fallback,
leave `:162`). Sound reasoning — the wire format is unchanged, so a v1 client talks to a v4 server
fine, and the only coupling was the shared venv.

**The user chose the full port instead**, with the trade-offs stated explicitly: it is a behaviour
change on the authenticated path, httpx2 becomes a nocobot runtime dep, and nocobot has only 29
tests of unknown `mcp_client` coverage. Chosen to keep one venv and one suite.

Required work: rename the transport; move the bearer into a constructed `httpx2.AsyncClient`;
`:162` → `is_error`; `:103` → `input_schema` with the fallback **deleted**; declare httpx2; bound
`mcp>=2,<3` (**not** unbounded — `mcp>=1.0.0` unbounded is what created this); refresh `uv.lock`
onto v2; handle the diverged `sse_client` path explicitly.

**Acceptance gate:** a test proving the `Authorization` header actually reaches the outbound request
under v2. Importing cleanly proves nothing. This is the nocobot analogue of T5 — in the failure mode
being guarded against, the bot connects, tools list, calls succeed, and the only symptom is that
`MCP_API_KEY` silently stopped being enforced.

### 6.7 Three Phase 3 corrections to earlier amendments

1. **§6.2(b) had the boundary wrong.** The `cannot import name 'FastMCP'` ImportError did **not**
   occur on 3.4.7 → 4.0.5; no `--force-reinstall` was needed. The bug is the fastmcp/fastmcp-slim
   meta-package split at **3.2→3.3**, which Phase 1 crossed and Phase 3 does not. Prediction sound,
   boundary misplaced.
2. **§6.4's harness-port worry did not materialise.** All 12 Phase-1 tests pass on 4.0.5 with
   **zero edits**, raw httpx `ASGITransport` and all. No port to `fastmcp.utilities.tests` needed.
   Worth knowing: httpx 0.28.1 now survives in the venv only via litellm/python-telegram-bot, since
   fastmcp 4 pulls httpx2 — the `test` extra declaring `httpx>=0.25.0` explicitly is what keeps a
   fresh install working.
3. **§4.2's UNVERIFIED bridge is now VERIFIED.** `tool.inputSchema` through a fastmcp `Client`
   emits `FastMCPDeprecationWarning` and returns the correct value, exactly as documented.

Also: `mcpserver_test.py:308,326` read `tool.inputSchema`. They postdate the report and so were
absent from the 8-site list; they become hard failures under `FASTMCP_MCP_CAMELCASE_COMPAT=False`
and are fixed to `.input_schema` with assertions unchanged.

**4.0.5 delta (§1 staleness warning, resolved):** benign. The only substantive change is
"Preserve field-level strict validation in lax mode" (honours `Field(strict=True)`/`StrictInt` —
zero occurrences in this repo), plus a regression test for the OAuthProxy ID-JAG guard (no
OAuthProxy here). Note the repo moved to **PrefectHQ/fastmcp**; `jlowin/fastmcp` redirects.

### 6.8 Phase 3 complete (`f48d507`) — nocodb is on FastMCP 4.0.5

Architect-verified: `pytest nocodb/` → **136 passed** (123 SDK + 13 MCP); repo-root suite correctly
does **not** collect; `nocobot/` carries no Phase 3 residue (its only diff from `pre-fastmcp4` is
Phase 2's `:218` docstring fix from `92d495c`, working tree clean).

**Dependencies:** fastmcp 3.4.7 → 4.0.5, mcp 1.30.0 → 2.2.0, plus new mcp-types 2.2.0, httpx2
2.13.0, httpcore2 2.13.0, truststore 0.10.4. **Unchanged:** cyclopts 4.25.3, pydantic 2.13.5,
starlette 1.6.0, uvicorn, Authlib, httpx 0.28.1 — §6.2(c)'s cascade had already done the heavy
lifting, so the 4.x bump only added the SDK v2 tree alongside. No `--force-reinstall`, no
ImportError, confirming §6.7(1).

**Floors:** `fastmcp>=4.0.5,<5` at all four sites (three extras + `test`). Floor equals tested
version per §6.1. Capped at `<5` for the Phase 0 reason. **B2/B3 need no declaration in nocodb** —
fastmcp-slim 4.0.5 declares `pydantic[email]>=2.12.0` and `starlette>=1.0.1` itself, satisfying them
transitively.

**`generated.py` needed no hand-patching.** The 4.x generator emits snake_case natively;
regeneration alone fixed all five sites plus `import mcp.types` → `import mcp_types`. 56-line diff,
100% the SDK v2 rename. All five hardened assertions matched first try and the name-set gate passed
at 62. **`skill.md` is byte-identical at 28211** — §6.5's template-change concern did not recur.

**Lockfile, no escalation needed.** `uv pip compile setup.py --extra mcp` works directly on
`setup.py`; no packaging conversion. 72 pins in `nocodb/requirements-mcp.txt`. Dockerfile ported to
the nocobot base image, removing the unpinned `pip install uv`.

*Deviation worth knowing:* uv 0.10.7 has no `--check` on `pip compile`, so there is no direct
`--locked` equivalent for a `setup.py` project. Equivalent guarantee obtained by re-resolving
`.[mcp]` with `--offline` after install — which can only succeed if every specifier is already
satisfied by what the lockfile installed. **Proven in both directions inside Docker:** clean build
exits 0; with `fastmcp>=99` the build exits 1 at that layer. Image verified *running*, not merely
building — `/health` 200, 62 tools listed in-container.

**Tests: 13, not 12.** All 12 pass on 4.0.5 with **zero edits**, T5 included, before anything was
touched. Only change: `:308`/`:326` → `.input_schema`, assertions identical.

**T0 added — approved, keep it.** `conftest.py` sets `FASTMCP_MCP_CAMELCASE_COMPAT=False`; T0
asserts `settings.mcp_camelcase_compat is False`. Without it, a renamed-upstream or mistyped env var
leaves the bridge **on**, every surviving camelCase read keeps passing, and the suite certifies a
migration it never tested. That is the same fail-open shape as the `62 == 62` count check (§4.3) and
the permissive `validate=` default (§4.5) — a check that cannot fail is not a check. Phase 3 flagged
it rather than slipping it in, which is the right instinct.

**Residual greps all clean:** `.ping(` 0, `-32002` 0, full removed-API sweep 0 (§3.2 holds on 4.x),
camelCase in `nocodb/` 0 code hits, `mcp.types` 0 after regen.

Also updated six stale "FastMCP 3.0/3.x" current-state references and `DEPLOY_MCP.md`'s
expected-build-output block. **Dated changelog lines left alone deliberately** (README.md:19,
nocodb/README.md:18) — they record a Feb 2026 event and rewriting them would falsify history.

### 6.9 TENTH ERROR — both advertised `fastmcp` commands are broken on 4.x

`mcpserver/__init__.py:7-8` advertised `fastmcp run nocodb.mcpserver.server:mcp` and
`fastmcp dev nocodb.mcpserver.server:mcp`. Neither works:

- **`fastmcp run`** resolves a bare spec as a **filesystem path**. The dotted form errors
  `File not found`. The file form `server.py:mcp` also fails —
  `attempted relative import with no known parent package` — because `server.py` imports its
  siblings relatively and only loads as part of the package (§5.1's deliberate circular import).
  **Working form: `fastmcp run -m nocodb.mcpserver`** (verified, server starts).
- **`fastmcp dev` is a COMMAND GROUP as of 4.x** — architect-verified:
  `Usage: fastmcp dev COMMAND`, subcommands `apps` and `inspector`. `fastmcp dev <target>` errors
  `Unknown command`. **Working form: `fastmcp dev inspector -m nocodb.mcpserver`.**

Docstring fixed to the working forms. **Honest limitation, stated by Phase 3:** it could not
establish whether the dotted form ever worked on 3.x — the corpus has no `/v3/` mirror of the CLI
page. So the docstring documents what works on the installed version without claiming when it broke.
The `dev` group change is definitely 4.x.

### 6.10 Handoff state for the nocobot agent

Phase 3 started two nocobot edits before the reassignment and **reverted both** (architect-verified).
nocobot is at a clean, known state:

- `mcp_client.py:103` — `hasattr(...) else {}` fallback **still present**
- `mcp_client.py:162` — `result.isError` **still present**
- `pyproject.toml:22` — back to **unbounded `mcp>=1.0.0`**

**⚠️ That last one is a live exposure.** A `uv lock --upgrade` on nocobot today pulls mcp 2.2.0 and
the bot dies at import. It is Phase 0's problem, still open on the other service, and it now belongs
to the nocobot agent. The transport port was never started, so there are no httpx2 notes to inherit
— and under the `fastmcp.Client` reframe there would be no use for them anyway.

**Three findings Phase 3 hands over that are not in §6.6:**

1. **`sse_client` survives v2 with `headers=`/`timeout=` intact** (signature verified). The two
   transports genuinely diverge — `_open_transport()` at `:45-49` cannot stay symmetric.
2. **SDK v1 has no snake_case aliases at all** — the mcp 1.30.0 wheel's `types.py:1320`
   `inputSchema`, `:1369` `isError`, no `populate_by_name`, no `alias_generator`. There is no
   version of nocobot that reads both spellings. It is a hard cutover.
3. **`hasattr(c, 'text')` at `:159` is NOT a camelCase defect.** It is a legitimate content-block
   discriminator and `.text` is unchanged in v2. **Easy to over-correct — do not touch it.**

#### Phase 3 note: `result.is_error` needs no bridge

Post-regen camelCase sites in `generated.py` are unchanged: `:56`, `:59` (`block.mimeType`),
`:91-92` (`tool.inputSchema`), `:133`, `:177` (`msg.content.mimeType`). But `:39` and `:72` read
`result.is_error`, which is **already snake_case in both generators** — no bridge needed there.

---

## 6.11 nocobot complete (`bad76bf`) — and Phase 4 PASSED

**Architect-verified.** Repo-root suite collects again: **174 passed / 57 skipped**
(136 nocodb + 29 nocobot existing + 9 new). `uv export --locked` exits 0 against the regenerated
lock. The unbounded `mcp>=1.0.0` exposure from §6.10 is closed — `mcp` and `httpx` dropped as direct
deps, `fastmcp>=4.0.5,<5` added.

**Auth mutation independently reproduced by the architect.** Dropping `auth=` from `_build_client`:

```
FAILED nocobot/mcp_client_test.py::test_authorization_header_reaches_the_server
1 failed, 8 passed
...while the client logged "Discovered 3 MCP tools" and "Cached 1 MCP resources"
```

The client connected and worked **with no auth at all**. Exactly one assertion noticed. That is the
T5 shape reproduced in the second service. The timeout is mutation-proven too.

### ⚠️ Harness finding: `asgi_server` does NOT work for outbound-request assertions

Its own docstring: *"nothing is listening on the network, a plain `httpx2.AsyncClient()` cannot
reach this server."* `MCPClient` builds its transport internally, so there is no seam to inject the
ASGI bridge without changing production code. **The spec's suggested approach was wrong.**

Working approach: `run_server_in_process` — a real uvicorn on a real port, with the probe tool
returning the captured header via `get_http_headers(include={"authorization"})` **as its result**,
so nothing crosses the process boundary except the MCP response. ~1.3s for the file.
**Do not hand `asgi_server` to a future agent for this shape of assertion.**

### The compat flag strengthened this migration for free

`conftest.py` sets `FASTMCP_MCP_CAMELCASE_COMPAT=False` for the whole session, so the bridge was
**off** for every nocobot run. The snake_case reads are not merely preferred over a deprecated
bridge — under this suite a missed camelCase read is a **hard failure, not a warning**. Phase 3's
conftest change silently raised the acceptance bar for work that came after it, which is the
compounding benefit of building the net before doing the migration.

---

## 7. Phase 4 — live verification (architect, 2026-09-17)

Real server, `python -m nocodb.mcpserver --http`, dummy credentials only. **Nothing touched the
live NocoDB instance.**

| Check | Result |
|---|---|
| `/health` | `200 {"status":"ok"}` |
| `/mcp` wrong bearer | **401** |
| `/mcp` no bearer | **401** |
| `/mcp` correct bearer | **200** |
| nocobot E2E — tools discovered | **62** |
| nocobot E2E — transform tools | `['list_resources', 'read_resource']` both present |
| nocobot E2E — resources cached | **3** |
| nocobot E2E — tools with empty schema | **none** ← the `:103` bug would surface here |
| nocobot E2E — wrong API key | rejected (`MCPError`) |

The empty-schema check is the one that closes the loop on §4.1. The original defect shipped `{}` as
every tool's schema to the LLM; a live end-to-end run through the rewritten client now proves all 62
carry real parameter schemas.

**Not covered by Phase 4:** a real Telegram round-trip and a deploy to Dokploy. Both need live
credentials and are the user's call.

---

## 8. Open items — user decisions, none blocking

1. **`tests/` is gitignored** (`.gitignore:15`), so Phase 1's `NOCODB_RUN_INTEGRATION` guard lives
   only in the working copy and will not survive a fresh clone. Recommendation: keep it ignored
   (files may carry real NocoDB details); decide between a documented local-only harness, or moving
   credential-free parts into tracked colocated tests.
2. **Lost `skill.md` prose** (§6.5). The 3.4.7 generator dropped every `Returns:` block and the
   filter-syntax prose (39044 → 28211 bytes). The 4.x hop caused no *further* loss — byte-identical
   — but the original loss stands. Fix belongs in a post-processing step or companion doc, never a
   hand-edit of generated output.
3. **Live-instance residue check** after the Phase 1 incident (§6.4). Reported clean by that agent;
   never independently confirmed, since that means connecting to production.
4. **`DEPLOY_MCP.md` build-path contradiction** (§2.4): `:31,45` say Build Path `/` + context
   `nocodb`; `CLAUDE.md:13` says `/nocodb/`. The Dockerfile only works with context `nocodb/`, and
   the new `.dockerignore` assumes it. **Worth resolving before the next deploy.**
5. **Unfixed, deliberately:** `require_confirm` dead code (`errors.py:43-66`), the hardcoded `/mcp`
   path (`regenerate-cli.sh:56`, `nocobot/config.py:20`), nocobot's broken editable install (§6.3),
   the pre-existing `AsyncMock` coroutine warning in `nocobot/agent_test.py:28`, and CI (none
   exists — nothing runs these 174 tests on push).

---

## 9. Rules for every phase agent

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
