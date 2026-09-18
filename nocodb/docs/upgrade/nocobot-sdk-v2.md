# nocobot — adopt `fastmcp.Client` (supersedes the raw SDK v1→v2 port)

**Agent:** `nocodb-mcp-v2-protocol-upgrade`
**Prerequisite reading:** `nocodb/docs/upgrade/FASTMCP4-UPGRADE-REPORT.md` **§6.6, §6.7**.
**Depends on:** Phase 3's nocodb-side commit. **Do not edit until the architect gives the go
signal** — Phase 3 is active in this repo.
**Branch:** `fastmcp-4-upgrade`. Not master. Rollback: tag `pre-fastmcp4`.

---

## Read this first — the approach changed

An earlier draft of this brief sent you to hand-port nocobot's raw MCP SDK transport: rename
`streamablehttp_client`, build an `httpx2.AsyncClient`, move the bearer header onto it.
**That was the wrong frame and is superseded.**

**The server nocobot talks to is FastMCP 4.0.5, not a raw-protocol server.** The first-party client
for a FastMCP server is `fastmcp.Client`. `nocodb/cli/generated.py:16` already uses exactly that.
nocobot is the odd one out, hand-rolling raw-SDK plumbing to talk to a FastMCP server.

So the job is **not** "port the transport". It is **"stop hand-rolling a client"**.

### Why this is better, concretely

`fastmcp.Client.__init__` (verified against installed 4.0.5) takes:

```
auth: httpx2.Auth | Literal['oauth'] | str | None = None
timeout: datetime.timedelta | float | int | None = None
auto_initialize: bool = True
```

`fastmcp-full.txt:2172`: *"The most straightforward way to use a pre-existing Bearer token is to
provide it as a string to the `auth` parameter... FastMCP will automatically format it correctly for
the `Authorization` header and bearer scheme."*

So the entire hazardous part of the old plan — manually constructing the auth header, hand-building
an `httpx2.AsyncClient`, carrying the timeout across a changed signature — **collapses into two
keyword arguments.** You are deleting the risky code, not rewriting it.

It also removes the raw-SDK version coupling that caused this whole situation: nocobot stops
depending on `mcp` directly and depends on `fastmcp`, the same library the server is built on.

### API surface check — confirmed, but the framing was incomplete

nocobot uses exactly five session calls: `initialize` (`:67`), `list_tools` (`:96`),
`list_resources` (`:110`), `read_resource` (`:113`), `call_tool` (`:137`). **All are first-class on
`fastmcp.Client`**, and `auto_initialize=True` covers `initialize`. No capability is lost.

**But "nothing is lost in the swap" undersold the edit.** Three of the five changed **return
shape** — fastmcp unwraps the protocol result objects:

| Call | Raw SDK returns | `fastmcp.Client` returns | Breaks |
|---|---|---|---|
| `list_tools()` | `ListToolsResult` | `list[Tool]` | `:96-97` `tools_result.tools` |
| `list_resources()` | `ListResourcesResult` | `list[Resource]` | `:110-112` `resources_result.resources` |
| `read_resource()` | `ReadResourceResult` | `list[TextResourceContents \| Blob]` | `:113-115` `content.contents` |

Verified live against the real server: 62 tools, 3 resources, 1 content item. These are loud
`AttributeError`s, so the risk is low — but `_discover` is **three unwrap changes plus the field
renames**, not "two field renames". Scope accordingly.

**Non-issue, checked anyway:** `ResourcesAsTools` only *adds* to `list_tools`; it does not override
protocol-level `resources/list`. `list_resources()` still returns all 3 `nocodb://` resources, so
nocobot's resource cache and system prompt are unaffected. Worth stating because CLAUDE.md's
"not exposed individually" phrasing reads like it might hide them. It doesn't.

---

## Scope

1. **Replace the transport + session plumbing with `fastmcp.Client`.**
   - `mcp_client.py:12` — drop `from mcp.client.streamable_http import streamablehttp_client`
     (and the `sse_client` import if the SSE path goes too — see item 2).
   - `:32` — delete the hand-built `{"Authorization": f"Bearer {api_key}"}` dict. Pass the key to
     `Client(auth=api_key)` instead.
   - `:45-49` `_open_transport()` and the `AsyncExitStack`/`ClientSession` dance at `:62-67` —
     replace with a `Client`. Keep the existing reconnect/lock/caching behaviour around it; you are
     swapping the client, not redesigning `NocoDBMCPClient`.
   - **Carry `timeout=3600` onto the `Client`.** It is currently passed at `:48`/`:49` and is
     deliberate for a long-lived bot connection. Do not let it default — see the trap below.

2. **Decide the SSE path deliberately and say what you chose.** `:41-48` branches on a `/sse` URL
   suffix. `fastmcp.Client` infers transport from the URL, so this branch may become unnecessary.
   Either keep an explicit transport selection or let `Client` infer it — **but state which, and
   confirm the `/sse` URL shape still works.** Do not delete the branch silently.

3. **Field renames — still do them.** `:103` → `input_schema`, `:162` → `is_error`.
   - `fastmcp.Client` gives you the camelCase compat bridge (Phase 3 verified it: returns the right
     value, emits `FastMCPDeprecationWarning`), so the old spellings would *work*. **Use snake_case
     anyway** — the bridge is deprecated and scheduled for removal (`fastmcp-full.txt:32557-32580`).
   - **`:103` — delete the `hasattr(...) else {}` fallback entirely.** Do not repoint the guard.
     It shipped `{}` as every tool's schema to the LLM, degrading the agent to guessing parameters
     with no error trail — a silent fallback masking a hard failure, against the Fail Fast rule in
     `~/.claude/CLAUDE.md`. A missing schema is worth raising.

4. **Dependencies.** Declare `fastmcp` in `nocobot/pyproject.toml` with a bound (`>=4,<5` — match
   whatever Phase 3 settled on for nocodb; check its commit). Remove the direct `mcp>=1.0.0` at
   `:22` if nothing else in nocobot imports `mcp` directly — **verify with grep, don't assume**.
   Consider `fastmcp-slim` if image size matters (same `import fastmcp`, minimal deps, opt-in
   extras — `fastmcp-full.txt:38900-38914`). Check whether `httpx>=0.25.0` at `:26` is still used.
   **Do not leave any new dependency unbounded** — an unbounded `mcp>=1.0.0` is what created this
   situation in the first place.

5. **Refresh `nocobot/uv.lock`.** `nocobot/Dockerfile:6-7` uses `uv export --locked`, which fails
   the build loudly on drift. Make sure it is genuinely regenerated.

---

## ⚠️ The timeout trap — right conclusion, corrected number

**CORRECTED.** An earlier draft cited a **flat 5 seconds** as the cost of omitting the timeout. That
figure is wrong for the path we are now taking, and the correction matters because the number was
cited as evidence.

Architect-verified:

| Path | Default if you omit the timeout |
|---|---|
| Hand-built bare `httpx2.AsyncClient()` — the **old raw-SDK plan** | `Timeout(5.0)` — the 5s figure was correct *for that plan* |
| `fastmcp.Client` — **what you are doing** | `httpx2.Timeout(30.0, read=300.0)` (`mcp/shared/_httpx_utils.py:13-14,58`) |

**fastmcp never hands you a bare client**, so 5s does not apply. The real cost of omitting it is a
**300-second read timeout** against an intended 3600.

**The conclusion is unchanged: carry it and assert it.** A long-lived GET stream that drops after
five idle minutes produces exactly the symptom described — flaky reconnects, no error at the call
site, nothing in a health check. It is a real regression, just a less dramatic one than stated.

Confirmed upside: **`Client(timeout=3600)` covers both layers.** `connect_session` builds
`httpx2.Timeout(30.0, read=3600)` *and* sets the session's `read_timeout_seconds`. Connect, write
and pool stay at 30s, which is what you want. One kwarg genuinely does it.

---

## ⚠️ `raise_on_error=True` is the default — pass `raise_on_error=False`

**Architect-verified:** `Client.call_tool(..., raise_on_error: bool = True)`.

A failing tool therefore **raises `fastmcp.exceptions.ToolError`** rather than returning a result
with `is_error=True`. In nocobot that exception lands in the `except Exception` at `:151`, which
returns a generic *"Tool call failed. Please try a different approach."*

Two consequences, and this is the subtle one in this migration:

1. **The `:162` `is_error` branch becomes dead code.** Renaming it to `is_error` as the scope
   instructs would leave a correct-looking rename on a line that never executes.
2. **The `:163` warning that logs the actual server error text stops firing** — the error detail
   disappears from the logs, replaced by a generic string.

That is a silent behaviour change on the error path: nothing crashes, the bot keeps answering, and
diagnostics quietly get worse.

**Pass `raise_on_error=False`.** Verified to restore exactly the current semantics — `is_error=True`
with the error text in `result.content` — keeping `:162` meaningful and preserving the logging.

---

## ⚠️ The acceptance gate

**A test proving `Authorization: Bearer <key>` actually reaches the outbound request.**

Making it import cleanly proves nothing. In the failure mode being guarded against, the bot
connects, lists tools, and calls succeed — because the server accepts the request anyway. The only
symptom is that `MCP_API_KEY` has silently stopped being enforced. Nothing in a log or health check
would reveal it.

This is the direct analogue of nocodb's T5 (§4.5, §6.4). Phase 1 proved T5 could fail by mutating
the code under it and watching exactly one test go red. **Hold yourself to that standard: show the
auth test failing when the auth is wired wrong, then passing when it is right.**

Passing `auth=api_key` is *less* error-prone than the old header dict — but "less error-prone" is
not "verified", and this is the one path where a silent failure is a security outcome.

### ⚠️ The trap inside the gate

`auth=<str>` becomes a `BearerAuth` that sets the header inside `auth_flow()` at **request time**.
It is **not** a static header on the client. So an assertion against `client.headers` would **pass
vacuously and prove nothing** — the exact failure mode this gate exists to prevent, reproduced
inside the gate itself.

The test must observe a **real outbound request**. Workable approach:
`fastmcp.utilities.tests.asgi_server(server)` gives a real in-process port, and a probe tool can
capture what the server actually received via
`get_http_headers(include={"authorization"})` — **the `include=` is required**, since
`get_http_headers()` filters auth headers by default.

Then mutate: drop `auth=`, watch that one test go red, restore.

---

## Reference material on disk

| File | Size | Use |
|---|---|---|
| `nocodb/docs/fastmcp-full.txt` | 2.8 MB, 1276 sections | **Grep only.** FastMCP 4 docs — client auth at `2154-2210`, Client/transport reference, camelCase bridge at `32557-32580`, slim vs full at `38900-38914`. **This is your primary reference.** |
| `nocodb/docs/fastmcp.txt` | 63 KB | FastMCP index, safe to read whole |
| `nocodb/docs/mcp-sdk-full.txt` | 776 KB, 14370 lines | **Grep only.** Raw MCP Python SDK docs. Now mostly *background* — you are moving off the raw SDK. Still useful for understanding what changed underneath: v1→v2 transport recipe at `3479-3527`, error lookup table at `1440-1458`. |
| `nocodb/docs/mcp-sdk.txt` | 4.8 KB | SDK index, safe to read whole |

Both SDK files fetched 2026-09-17 from `https://py.sdk.modelcontextprotocol.io/llms.txt`. All four
are gitignored — vendored upstream docs, not source.

### Raw-SDK context, for background only

You are no longer doing this port, but it explains why nocobot broke. Under `mcp` 2.2.0:
`streamablehttp_client` → `ImportError`; the replacement `streamable_http_client(url, *,
http_client, terminate_on_close)` dropped `headers=` and `timeout=`; and SDK v2 renamed protocol
fields camelCase → snake_case with **no aliases on v1** (Phase 3 inspected the 1.30.0 wheel:
`types.py:1320` `inputSchema`, `:1369` `isError`, no `populate_by_name`).

Two non-issues, already checked: the 3-tuple→2-tuple change is harmless because `:65` reads
`transport[0], transport[1]` by index rather than unpacking; and `follow_redirects` is handled by
the transport (`mcp-sdk-full.txt:3519`).

---

## Verification

**Success looks like the shared venv working again.** nocodb on FastMCP 4 needs `mcp>=2`; nocobot's
*current* code needs `mcp<2`. That incompatibility is why `venv/bin/python -m pytest -q` currently
dies with `ERROR nocobot/agent_test.py — Interrupted: 1 error during collection`, **zero tests run**.
Your commit closes that window. Baseline before the break was **164 passed / 57 skipped**, plus
whatever you add.

- **Check what nocobot's 29 existing tests actually cover** (telegram 15, agent 10, retry 4). Do not
  assume they touch `mcp_client`. Report what you find.
- **NEVER run `pytest` with `NOCODB_RUN_INTEGRATION=1`.** Those 57 tests create and delete a real
  base on the user's live NocoDB. In Phase 1 an `env -u NOCODB_URL -u NOCODB_TOKEN` command failed
  to suppress credentials because `tests/test_integration_full.py:22` calls `load_dotenv()` and
  repopulated them from disk — the destructive suite ran against production. **Unsetting a variable
  cannot protect you from a module that reads credentials off disk.** Plain
  `venv/bin/python -m pytest -q` is safe. For a server without live credentials use explicit dummies
  (`NOCODB_URL=https://example.invalid NOCODB_TOKEN=x NOCODB_BASE_ID=b`).

---

## Out of scope — report, do not fix

- Anything under `nocodb/` — Phase 3's, and it is active in this repo
- **nocobot's broken editable install** (§6.3): `pyproject.toml` sets `packages = ["nocobot"]` but
  sits *inside* the package dir, so hatchling resolves `nocobot/nocobot`, which does not exist.
  Local `import nocobot` works only because pytest puts rootdir on `sys.path`. Production is
  unaffected — `nocobot/Dockerfile:9-14` rebuilds the hierarchy at COPY time deliberately. You will
  be in `pyproject.toml` for item 4 and it will be tempting. **Don't** — separate blast radius,
  explicitly unassigned.
- The hardcoded `/mcp` path at `nocobot/config.py:20` (§4.6)
- CI workflows

---

## Definition of done

- [ ] `fastmcp.Client` adopted; raw transport + `ClientSession` plumbing deleted
- [ ] `auth=api_key` replaces the hand-built header dict
- [ ] `timeout=3600` carried explicitly and **asserted in a test**
- [ ] SSE path decision made and stated
- [ ] `:103` fallback **deleted**, `:162` renamed, both snake_case natively
- [ ] Dependencies declared and **bounded**; `mcp`/`httpx` direct deps removed if genuinely unused
- [ ] `uv.lock` regenerated
- [ ] **Auth test proving the header reaches the request**, with mutation evidence it can fail
- [ ] What nocobot's existing 29 tests actually covered, reported
- [ ] Repo-root `pytest` collects again; combined counts reported
- [ ] Committed (do **not** push)

## Commit

Do not commit `nocodb/docs/fastmcp*.txt` or `mcp-sdk*.txt` (gitignored), `.claude/`, or
`reddit-post-draft.md`.

```
refactor(nocobot)!: talk to the server through fastmcp.Client

nocobot hand-rolled a raw MCP SDK client - transport, session and
a manually built Authorization header - to talk to a server that
is itself built on FastMCP. SDK v2 then renamed the transport and
dropped headers= and timeout=, breaking that plumbing outright.

Rather than port the hand-rolled client, this adopts fastmcp's
own Client, which takes the bearer token as auth= and the timeout
as a first-class argument. The riskiest part of the migration -
reconstructing the auth header by hand - is deleted rather than
rewritten.

Also renames the protocol field reads to snake_case rather than
leaning on the deprecated camelCase bridge, and deletes the
hasattr fallback at :103 that silently shipped {} as every tool's
schema to the LLM.

BREAKING CHANGE: nocobot now depends on fastmcp.

Refs: nocodb/docs/upgrade/FASTMCP4-UPGRADE-REPORT.md section 6.6
```

## If stuck

Grep **`nocodb/docs/fastmcp-full.txt`** — client auth at `2154-2210` is your starting point. Then
escalate to `nocodb-upgrade-architect`.

**Escalate rather than improvising on:** anything that would change `NocoDBMCPClient`'s external
behaviour beyond the client swap, any auth assertion you cannot make pass, and any capability you
find missing from `fastmcp.Client` — the architect verified all five of nocobot's session calls
exist on it, so a gap there means that check was wrong and I need to know immediately.

Four agents have found nine errors in the report so far. If you find a tenth, say so.
