# Phase 0 — Cap the FastMCP pin at `<4`

**Agent:** `nocodb-phase-0`
**Prerequisite reading:** `nocodb/docs/upgrade/FASTMCP4-UPGRADE-REPORT.md` — read it **in full** first.
**Baseline:** tag `pre-fastmcp4` (`d7a5726`). Rollback: `git reset --hard pre-fastmcp4`.

---

## Why this phase exists

Read report §2.4. Right now:

- `nocodb/Dockerfile:10` runs `uv pip install --system -e ".[mcp]"` — resolving against **live PyPI
  on every build**, with no lockfile anywhere under `nocodb/`.
- `nocodb/setup.py` declares `fastmcp>=3.0.2` with **no upper bound**, at three separate sites.
- FastMCP 4.0.0 shipped 2026-08-31 and 4.0.4 is current, so `>=3.0.2` **already resolves to 4.x**.
- `nocodb/docs/DEPLOY_MCP.md:200-204` documents **Auto Deploy on push**.

**Net: a README edit can ship an untested major version to production.** There are zero tests
covering the MCP layer (report §2.5) and no CI (report §2.6), so nothing would catch it.

This phase is a few characters of change. It is first because it is the only thing standing between
an unrelated push and an unplanned production upgrade. Do not expand it.

---

## Scope — do exactly this

### 1. Add the upper bound

In `nocodb/setup.py`, change the FastMCP specifier at **all three** sites:

| Line | Extra | From | To |
|---|---|---|---|
| 47 | `cli` | `fastmcp>=3.0.2` | `fastmcp>=3.0.2,<4` |
| 51 | `mcp` | `fastmcp>=3.0.2` | `fastmcp>=3.0.2,<4` |
| 54 | `all` | `fastmcp>=3.0.2` | `fastmcp>=3.0.2,<4` |

Read the file first and confirm the line numbers still match before editing — do not edit blind.
**All three must change.** Missing one leaves the `all` or `cli` path able to pull 4.x.

### 2. Add a comment at each site

One short line noting the cap is deliberate and pointing at the upgrade plan, e.g.
`# Capped pending FastMCP 4 migration - see docs/upgrade/FASTMCP4-UPGRADE-REPORT.md`.
Match the file's existing comment style (see the existing comment at `setup.py:46`).

### 3. Verify the cap actually binds

Produce **real evidence** that a fresh resolve now selects 3.x and not 4.x. Suggested:

```bash
printf 'fastmcp>=3.0.2,<4\n' > /tmp/p0-check.txt
uv pip compile /tmp/p0-check.txt 2>&1 | grep -i '^fastmcp'
```

Then confirm the *uncapped* spec would have picked 4.x, so the cap is demonstrably doing work:

```bash
printf 'fastmcp>=3.0.2\n' > /tmp/p0-check-uncapped.txt
uv pip compile /tmp/p0-check-uncapped.txt 2>&1 | grep -i '^fastmcp'
```

Paste both outputs in your report. The contrast **is** the proof. If `uv` is unavailable, any
equivalent resolver dry-run is fine — but you must show an actual resolved version number, not an
assertion that it should work.

### 4. Confirm nothing regressed

`venv/bin/python -m pytest -q` — expect the existing baseline. Record the pass/fail/skip counts.
Report §2.5 says 209 collected, 57 permanently skipped (missing `NOCODB_API_KEY`), so ~152 run.
**That skew is a known pre-existing condition — Phase 1 fixes it, not you.** Just confirm you did
not make it worse.

---

## Explicitly OUT of scope

Do not touch any of these. They are other phases' work or deliberate non-goals:

- `requests>=2.0` and every other unbounded specifier — noted in report §2.2, not this phase.
- Adding a lockfile or changing `nocodb/Dockerfile` — **Phase 3**.
- `nocodb/cli/generated.py` staleness — **Phase 2**.
- Any test additions — **Phase 1**.
- The `nocobot` camelCase bugs — **Phase 3**.
- `nocobot/pyproject.toml` — nocobot is already lock-protected (report §4.1). Leave it alone.

If you believe one of these blocks your phase, **escalate — do not proceed into it.**

---

## Definition of done

- [ ] All three `fastmcp` specifiers in `nocodb/setup.py` carry `,<4`
- [ ] A comment at each site explains why
- [ ] Resolver evidence captured showing capped → 3.x, uncapped → 4.x
- [ ] `pytest -q` run, counts recorded, no new failures vs baseline
- [ ] Committed (do **not** push)

## Commit

Scope the commit to `nocodb/setup.py` only. Do **not** commit `nocodb/docs/fastmcp*.txt` (2.9 MB of
vendored upstream docs — already gitignored), `.claude/`, or `reddit-post-draft.md`.

Suggested message:

```
build(nocodb): cap fastmcp at <4 pending 4.x migration

fastmcp>=3.0.2 was unbounded at three sites in setup.py while
nocodb/Dockerfile resolves against live PyPI on every build and
Dokploy auto-deploys on push. FastMCP 4.0.0 shipped 2026-08-31,
so any rebuild would have pulled an untested major version into
production with no MCP-layer tests and no CI to catch it.

Caps the cli, mcp, and all extras at <4. Lifted in phase 3.

Refs: nocodb/docs/upgrade/FASTMCP4-UPGRADE-REPORT.md
```

## If you get stuck

1. Grep `nocodb/docs/fastmcp-full.txt` (**never read it whole** — 2.8 MB).
2. Still unclear, or the report is wrong/missing something → escalate to
   `nocodb-upgrade-architect` via SendMessage. Do not guess and do not invent a workaround.

Report back: what you changed, the two resolver outputs, test counts, and the commit SHA.
