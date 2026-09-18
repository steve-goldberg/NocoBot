# Phase 1 — Build the MCP test net (still on 3.x)

**Agent:** `nocodb-phase-1`
**Prerequisite reading:** `nocodb/docs/upgrade/FASTMCP4-UPGRADE-REPORT.md` — read it **in full** first.
**Depends on:** Phase 0 committed.
**Runs against FastMCP 3.x.** Do not upgrade anything.

---

## Why this phase exists

Report §2.5: **209 tests, zero of which import FastMCP.** Nothing constructs a server, nothing
touches the 16 tool modules, nothing exercises `ResourcesAsTools`, `DebugTokenVerifier`,
`custom_route`, or `mcp.run()`. There is no `conftest.py` and pytest reports no configfile.

Phase 3 changes a major version of the framework this entire service is built on. **Right now there
is nothing that could tell you whether it worked.** You are building that instrument. These tests
must pass on 3.x now and are the acceptance gate for 4.x later — so write them against behaviour
that is true in both (report §3.3 lists what survives).

---

## Scope

### 1. Add `conftest.py` and fix pytest config

No `conftest.py` exists anywhere; pytest detects no configfile from the repo root, so
`nocobot/pyproject.toml:55-56`'s `asyncio_mode = "auto"` is **not applied** to collected async
tests. Fix this so async MCP tests run deterministically. Put pytest config where it applies to the
whole repo.

### 2. MCP server tests — `nocodb/mcpserver/mcpserver_test.py`

Follow the repo's colocated `*_test.py` convention (report §5.1, CLAUDE.md).

Use FastMCP's **in-memory client transport** against the real server object
(`from nocodb.mcpserver.server import mcp`) — no subprocess, no network, no live NocoDB. Grep the
docs for the in-memory / direct-server client pattern before writing:
`grep -n "in-memory\|FastMCP(\".*\")\|Client(mcp" nocodb/docs/fastmcp-full.txt`

Required assertions:

| # | Assertion | Why it matters |
|---|---|---|
| T1 | Exactly **63** tools are exposed (60 `@mcp.tool` + 3 from `ResourcesAsTools`) | Catches registration breakage and transform regressions. Report §5.1 has per-module counts (records 7, fields 6, view_filters 6, webhooks 6, tables 5, view_sorts 5, members 4, shared_views 4, view_columns 4, links 3, views 3, bases 2, schema 2, attachments 1, export 1, storage 1). |
| T2 | The 3 resources are reachable **and** surfaced as tools | Report §4 / changelog: `ResourcesAsTools` can degrade silently — server starts clean, just advertises 60 instead of 63. Nothing else would notice. |
| T3 | Every tool has a **non-empty** input schema | This is the exact failure shape of the `nocobot` bug (report §4.1) — an empty `{}` schema is silent and poisons the LLM. |
| T4 | `/health` returns `{"status":"ok"}` | It is the deploy gate. |
| T5 | **Auth REJECTS a wrong token** | ← **The single most important test here.** |
| T6 | Auth **accepts** the correct token | Proves T5 is testing auth, not a broken server. |

**On T5 — read report §4.5 before writing it.** `DebugTokenVerifier`'s `validate` parameter defaults
to a lambda that accepts *all non-empty tokens*; I verified this directly against the installed
3.0.0 class. `server.py:41-44` overrides that default. If the override were ever dropped, renamed,
or swallowed by a signature change, the server would construct fine, `/health` would still return
`ok` (it is a static handler that never touches auth), and `/mcp` would accept **any** bearer token.

A test that only asserts "correct token works" passes happily in that world. **Only a test that
asserts a wrong token is rejected can catch it.** T5 is the reason this phase is not optional.

Note `server.py:39` reads `MCP_API_KEY` from the environment **at import time**, so your test needs
to control the env before the module is imported. Handle that explicitly — do not skip T5 because
it is awkward to arrange. If you cannot make it work, escalate.

### 3. Fix the permanently-skipped integration tests

`tests/test_integration_full.py:39-42` gates on `NOCODB_URL` **and** `NOCODB_API_KEY`. The repo
`.env` has `NOCODB_URL`, `NOCODB_TOKEN`, `NOCODB_BASE_ID`, `NOCODB_VERIFY_SSL` — **`NOCODB_API_KEY`
does not exist**. So all 57 tests have been silently skipping.

Determine whether `NOCODB_API_KEY` is simply the wrong name for `NOCODB_TOKEN` (check what the tests
actually use, and what `nocodb/cli/config.py` and `mcpserver/dependencies.py` expect) and fix the
gate. **Do not paper over it** — if these tests need live credentials that are genuinely absent,
make the skip *explicit and loud* rather than silently conditional, and say so in your report.

Also: `tests/test_integration_full.py:21` imports `dotenv`, which is declared in neither
`nocodb/setup.py` nor `nocobot/pyproject.toml`. Declare it as a test dependency.

**`tests/` is gitignored** (`.gitignore:15`). So those 57 tests are *untracked as well as
permanently skipped* — invisible twice over, and absent from any fresh clone. Two consequences:

1. Put your new MCP tests at `nocodb/mcpserver/mcpserver_test.py` (colocated, tracked). **Do not
   put them under `tests/`** or they will not be committed.
2. Decide and report whether `tests/` being ignored is deliberate (a local-only live-credential
   harness) or accidental. **Do not un-ignore it unilaterally** — untracked test files may contain
   real NocoDB credentials. Flag it to the architect with a recommendation.

---

## Explicitly OUT of scope

- Any FastMCP version change, lockfile, or Dockerfile edit — **Phase 3**
- `nocodb/cli/generated.py` regeneration — **Phase 2**
- The `nocobot` camelCase fixes — **Phase 3** (write no tests that assume `input_schema`; you are
  on 3.x where it is `inputSchema`)
- Fixing `require_confirm` dead code (report §4.7) — report it, do not fix it
- Adding CI workflows — out of scope for all four phases; flag to the architect

---

## Definition of done

- [ ] `conftest.py` added; pytest config applies repo-wide; async tests run
- [ ] T1–T6 all implemented and **passing on FastMCP 3.0.0**
- [ ] T5 demonstrably fails if the `validate=` override is removed — **prove this**: temporarily
      drop the override, show the test fails, restore it, show it passes. Paste both results.
- [ ] Integration-test gate fixed or made explicitly loud; `dotenv` declared
- [ ] Full suite run; counts recorded and compared against the Phase 0 baseline
- [ ] Committed (do **not** push)

The T5 mutation check is the deliverable that matters. A test suite that passes but cannot fail on a
real defect is worse than no tests — it manufactures false confidence, which is precisely the
condition this repo is already in.

## Commit

Do not commit `nocodb/docs/fastmcp*.txt`, `.claude/`, or `reddit-post-draft.md`.

```
test(nocodb): add MCP server test coverage

The MCP layer had zero test coverage: none of the 209 existing
tests imported FastMCP or touched mcpserver/. Phase 3 bumps a
major version of the framework the service is built on, with
nothing able to observe a regression.

Adds in-memory client tests asserting 63 tools register, the 3
ResourcesAsTools resources are surfaced, every tool has a
non-empty input schema, /health responds, and auth rejects a
wrong token. Also fixes the integration-test gate, which
referenced a NOCODB_API_KEY env var that does not exist, so all
57 tests had been silently skipping.

Refs: nocodb/docs/upgrade/FASTMCP4-UPGRADE-REPORT.md
```

## If you get stuck

Grep `nocodb/docs/fastmcp-full.txt` (**never read whole**). Then escalate to
`nocodb-upgrade-architect`. Do not invent a workaround, and do not weaken an assertion to make it
pass — if a test cannot be made to work, say so and escalate.
