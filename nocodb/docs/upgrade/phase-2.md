# Phase 2 — Clear pre-existing drift (still on 3.x)

**Agent:** `nocodb-phase-2`
**Prerequisite reading:** `nocodb/docs/upgrade/FASTMCP4-UPGRADE-REPORT.md` — read it **in full** first.
**Depends on:** Phases 0 and 1 committed.
**Runs against FastMCP 3.x.** Do not upgrade anything.

---

## Why this phase exists

`nocodb/cli/generated.py` is committed output from `fastmcp generate-cli`, and it is **stale**
(report §4.3 — **read the correction block there, this section was wrong in the first draft**):

**THE COUNTS MATCH AND THE FILE IS STILL BROKEN.** Measured live by the architect:

```
generated.py commands: 62
live server tools    : 62

GHOSTS  (in CLI, not on server): ['get_reference', 'get_workflow_guide']
MISSING (on server, not in CLI): ['list_resources', 'read_resource']
```

**Compare name sets. Never counts.** A `62 == 62` assertion passes on this file — which exposes two
dead commands pointing at a deleted module and lacks the two commands that reach the 3 resources at
all. If you verify by counting, you will certify a broken artifact as correct.

- The ghosts are `get_workflow_guide` (`:1558`) and `get_reference` (`:1580`), from
  `nocodb/mcpserver/tools/docs.py`, **a module that has been deleted**.
- The missing pair is `ResourcesAsTools`-derived; the CLI predates that switch.
- Note `ResourcesAsTools` generates exactly **two** tools regardless of resource count — the 3
  resources are reached *through* `read_resource`, not exposed individually.
- Last regenerated at `c13aa72` (2026-03-11). The `ResourcesAsTools` switch (`09ddf0a`) and the
  formula-resource change (`327954e`) both landed 2026-03-12 **with no regen**.
- `nocodb/docs/CLI.md:3` still claims "62 commands".

The CLI is generated *by introspecting the running server*, so it is downstream of every FastMCP
change. Regenerating is how Phase 3 will detect breakage. **If you do not reconcile this drift
first, Phase 3 cannot distinguish an upgrade regression from damage that was already there.**

---

## Scope

### 1. Regenerate the CLI on 3.x

Run `nocodb/scripts/regenerate-cli.sh`. Pipeline (report §4.4): sources `.env`, picks a free port
from 9876, launches `python3 -m nocodb.mcpserver --http --port $PORT`, runs
`fastmcp generate-cli http://localhost:$PORT/mcp ... -f --timeout 60`, kills the server, then
regex-post-processes the emitted source.

Expected result: **62** commands whose **name set exactly equals** the live server's tool set —
`get_workflow_guide` and `get_reference` gone, `list_resources` and `read_resource` present.

Verify by set difference in both directions, not by counting. The architect's check:

```bash
NOCODB_URL=https://example.invalid NOCODB_TOKEN=x NOCODB_BASE_ID=b venv/bin/python -c "
import asyncio, re
from fastmcp import Client
from nocodb.mcpserver.server import mcp
gen = set(re.findall(r'@call_tool_app\.command\(name=[\"'\"'\"']([^\"'\"'\"']+)', open('nocodb/cli/generated.py').read()))
async def main():
    async with Client(mcp) as c:
        live = {t.name for t in await c.list_tools()}
    print('GHOSTS :', sorted(gen - live))
    print('MISSING:', sorted(live - gen))
asyncio.run(main())"
```

Both lists must be empty. If they are not, **stop and escalate** — do not hand-edit `generated.py`
to force agreement. It is generated output; a mismatch means the generator or the server is wrong,
and hand-patching would hide that from Phase 3.

### 2. Harden `regenerate-cli.sh` — it currently fails open

This is the most valuable change in the phase. Report §4.4:

The script post-processes generated source with regex surgery (`:62-97`), matching literal strings
like `app = cyclopts.App(name="localhost", help="CLI for localhost MCP server")`. **It prints
"Updated CLIENT_SPEC, app name, docstring" and exits 0 whether or not any regex matched.**

In Phase 3 a 4.x generator will likely emit a different template. Every substitution would silently
no-op, the script would report success, and a broken CLI would be committed.

Make each substitution **assert that it matched** and exit non-zero with a specific message if not.
Specifically the four at `:62-71` (CLIENT_SPEC → `StdioTransport`), `:74-78` (inject the
`StdioTransport` import), `:79-83` (inject `import os`), `:86-90` (rename the cyclopts app
`localhost` → `nocodb`).

Also fix the `sed` block at `:106-112`: it targets `cli/SKILL.md`, but the actual file is
`nocodb/cli/skill.md` (case mismatch) — another silent no-op. Make it fail loudly too.

### 3. Reconcile documented counts

- `nocodb/docs/CLI.md:3` — "62 commands" → correct value.
- Grep the repo for other stale counts (`CLAUDE.md` says "60 tools", `README.md`, `docs/MCP.md`,
  `mcpserver/__init__.py`). Be precise about the distinction: **60 `@mcp.tool` + 3 resource-derived
  = 63 CLI commands.** Both numbers are correct in their own context. Do not blindly overwrite 60
  with 63 — state which each document means.

### 4. Resolve the package version skew

> **SCOPE CHANGE (report §6.1).** The venv upgrade and editable-install repair that were originally
> yours **moved to Phase 1, step 0**. By the time you start, `fastmcp` should be **3.4.7**, the
> declared floor should read `fastmcp>=3.4.7,<4`, and the editable finder should point at the real
> path. **Verify all three on arrival** — if any is not true, Phase 1 did not finish its step 0 and
> you should escalate rather than doing it yourself.

What remains yours is the version-number skew only: `nocodb/__init__.py` declares
`__version__ = "3.1.0"` but the installed dist metadata says `nocodb 3.0.0` (report §2.1).

Decide and state whether that is a release that was never cut, or a version bump that was never
installed. **Do not silently renumber either side** — pick the correct one, say why, and make them
agree. Note `CLAUDE.md` also claims "v3.1.0 - Feature complete (123 tests)", while the suite
actually collects 209; fold that into your reconciliation in step 3.

---

## Explicitly OUT of scope

- Any FastMCP 4.x change, lockfile, or Dockerfile edit — **Phase 3**
- The `nocobot` camelCase fixes — **Phase 3**
- Adding new tests — **Phase 1** is done; only re-run and keep green
- `require_confirm` dead code (report §4.7) — report it, do not fix it
- The `/mcp` mount path hardcoding (report §4.6) — report it, do not fix it

---

## Definition of done

- [ ] `generated.py` regenerated: 63 commands, no `get_workflow_guide`, no `get_reference`
- [ ] `regenerate-cli.sh` fails loudly on every unmatched substitution — **prove it**: deliberately
      break one pattern, show a non-zero exit, restore, show success
- [ ] `skill.md` case mismatch fixed and no longer silently no-ops
- [ ] Documented counts corrected, with 60-vs-63 stated precisely
- [ ] Editable install repaired; `fastmcp` satisfies `>=3.0.2,<4`; version skew explained
- [ ] Phase 1 tests still green; full suite counts recorded
- [ ] Committed (do **not** push)

## Commit

Do not commit `nocodb/docs/fastmcp*.txt`, `.claude/`, or `reddit-post-draft.md`.

```
fix(nocodb): reconcile generated CLI drift and harden regen script

generated.py had been stale since c13aa72 (2026-03-11): 62
commands against a server exposing 63, still carrying
get_workflow_guide and get_reference from the deleted
tools/docs.py. The ResourcesAsTools switch and formula-resource
change both landed without a regen.

regenerate-cli.sh post-processes generated source by regex and
exited 0 whether or not anything matched, so a changed generator
template would silently produce a broken CLI. Each substitution
now asserts its match. Also fixes the sed block targeting
cli/SKILL.md when the real file is cli/skill.md.

Clears the baseline so phase 3 can attribute any CLI breakage to
the 4.x upgrade rather than pre-existing drift.

Refs: nocodb/docs/upgrade/FASTMCP4-UPGRADE-REPORT.md
```

## If you get stuck

Grep `nocodb/docs/fastmcp-full.txt` (**never read whole**). Then escalate to
`nocodb-upgrade-architect`. In particular: **escalate rather than hand-editing `generated.py`.**
It is build output, not source.
