# Phase 2 — Clear pre-existing drift (still on 3.x)

**Agent:** `nocodb-phase-2`
**Prerequisite reading:** `nocodb/docs/upgrade/FASTMCP4-UPGRADE-REPORT.md` — read it **in full** first.
**Depends on:** Phases 0 and 1 committed.
**Runs against FastMCP 3.x.** Do not upgrade anything.

---

## Why this phase exists

`nocodb/cli/generated.py` is committed output from `fastmcp generate-cli`, and it is **stale**
(report §4.3):

- It has **62** `@call_tool_app.command` entries; the server exposes **63** (60 tools + 3 from
  `ResourcesAsTools`).
- It still defines `get_workflow_guide` (`:1558`) and `get_reference` (`:1580`) — from
  `nocodb/mcpserver/tools/docs.py`, **a module that has been deleted**.
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

Expected result: **63** commands, with `get_workflow_guide` and `get_reference` **gone**, and the
3 `ResourcesAsTools`-derived entries present.

If the count is not 63, **stop and escalate** — do not hand-edit `generated.py` to force the number.
It is generated output; a wrong count means the generator or the server is wrong, and hand-patching
would hide that from Phase 3.

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

### 4. Fix the venv / editable-install drift

Report §2.1:
- Installed `fastmcp==3.0.0` is **below** the declared `>=3.0.2` floor.
- `nocodb/__init__.py` declares `__version__ = "3.1.0"` but dist metadata says `nocodb 3.0.0`.
- `__editable___nocodb_3_0_0_finder.py` points at `/Users/stevegoldberg/Code/Utils/nocodb/nocodb` —
  **a path that no longer exists** (repo moved to `Code/_utils/`). Imports resolve only because
  pytest puts rootdir on `sys.path`.

Reinstall the editable package so the finder points at the real path, and bring `fastmcp` up to a
3.x release that satisfies `>=3.0.2,<4` (Phase 0's cap must hold — verify it does).

Decide and state whether the `3.1.0` vs `3.0.0` skew is a release that was never cut or a version
bump that was never installed. Do not silently renumber.

**Re-run the Phase 1 test suite after reinstalling.** If those tests were passing on 3.0.0 and fail
on 3.0.2+, that is a real finding — report it, do not paper over it.

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
