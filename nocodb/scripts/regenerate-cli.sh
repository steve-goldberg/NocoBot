#!/bin/bash
# Regenerate the CLI from the MCP server using fastmcp generate-cli.
#
# Usage:
#   ./scripts/regenerate-cli.sh
#
# Requirements:
#   - fastmcp >= 3.4.7,<4
#   - NOCODB_URL, NOCODB_TOKEN, NOCODB_BASE_ID (via .env, env vars, or .nocodbrc)
#
# Fail-fast contract: every post-processing substitution asserts that it
# matched, and the run ends with a name-set comparison between the emitted
# commands and the live server's tools. A generator whose template changes, or
# a server/CLI drift, exits non-zero instead of reporting success on a broken
# artifact. Never relax an assertion to make a run pass -- a non-match means
# the generator or the server changed and the script needs updating.

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$PROJECT_DIR")"
export PROJECT_DIR

# Source .env if it exists
if [ -f "$REPO_ROOT/.env" ]; then
    source "$REPO_ROOT/.env"
fi

# Find an available port
PORT=9876
while nc -z localhost $PORT 2>/dev/null; do
    PORT=$((PORT + 1))
done

SERVER_PID=""
cleanup() {
    if [ -n "$SERVER_PID" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
        SERVER_PID=""
    fi
}
trap cleanup EXIT

echo "Starting MCP server on port $PORT..."
python3 -m nocodb.mcpserver --http --port $PORT &
SERVER_PID=$!
sleep 3

if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Error: MCP server failed to start"
    exit 1
fi

echo "Generating CLI from MCP server..."
if fastmcp generate-cli "http://localhost:$PORT/mcp" "$PROJECT_DIR/cli/generated.py" -f --timeout 60; then
    echo "Generated cli/generated.py"
else
    echo "Error: Failed to generate CLI"
    exit 1
fi

cleanup

# Post-process: CLIENT_SPEC -> StdioTransport, app name -> nocodb, skill.md naming.
# Each substitution asserts its match; a non-match exits non-zero.
python3 << 'EOF'
import os
import re
import sys
from pathlib import Path

project_dir = Path(os.environ["PROJECT_DIR"])
path = project_dir / "cli/generated.py"
if not path.exists():
    sys.exit(f"Error: generate-cli did not produce {path}")

content = path.read_text()
failures = []


def require_sub(pattern, replacement, label, *, count=1, expected=1):
    """Apply a regex substitution that MUST match, or record a failure."""
    global content
    new, n = re.subn(pattern, replacement, content, count=count)
    if n != expected:
        failures.append(
            f"{label}: expected {expected} match(es) for {pattern!r}, found {n}. "
            "The generator template has changed -- update this script."
        )
        return
    content = new


def require_present(needle, anchor, replacement, label):
    """Ensure `needle` ends up in the file, injecting at `anchor` if absent."""
    global content
    if needle in content:
        return
    new, n = re.subn(re.escape(anchor), replacement, content, count=1)
    if n != 1:
        failures.append(
            f"{label}: {needle!r} absent and anchor {anchor!r} not found. "
            "The generator template has changed -- update this script."
        )
        return
    content = new


# 1. CLIENT_SPEC: HTTP URL -> StdioTransport
require_sub(
    r"CLIENT_SPEC = 'http://localhost:\d+/mcp'",
    "CLIENT_SPEC = StdioTransport(\n"
    "    command=sys.executable,\n"
    '    args=["-m", "nocodb.mcpserver"],\n'
    "    env=os.environ.copy(),\n"
    ")",
    "CLIENT_SPEC -> StdioTransport",
)

# 2. StdioTransport import
require_present(
    "from fastmcp.client.transports import StdioTransport",
    "from fastmcp import Client",
    "from fastmcp import Client\nfrom fastmcp.client.transports import StdioTransport",
    "StdioTransport import",
)

# 3. os import (CLIENT_SPEC above uses os.environ)
require_present(
    "import os",
    "import sys",
    "import os\nimport sys",
    "os import",
)

# 4. cyclopts app name
require_sub(
    r'app = cyclopts\.App\(name="localhost", help="CLI for localhost MCP server"\)',
    'app = cyclopts.App(name="nocodb", help="NocoDB CLI - Agent-friendly command-line interface")',
    "cyclopts app name",
)

# 5. Module docstring
require_sub(
    r'"""CLI for localhost MCP server\.',
    '"""CLI for NocoDB MCP server.',
    "module docstring",
)

# --- skill.md -------------------------------------------------------------
# generate-cli writes `SKILL.md` next to the output file. The tracked file is
# `cli/skill.md`; on a case-insensitive filesystem (macOS APFS) those are the
# same inode, on Linux they are not. Resolve it case-insensitively, normalise
# to the tracked lowercase name, then apply the substitutions with assertions.
cli_dir = project_dir / "cli"
candidates = [p for p in cli_dir.iterdir() if p.name.lower() == "skill.md"]
if len(candidates) != 1:
    failures.append(
        f"skill file: expected exactly one skill.md in {cli_dir}, found "
        f"{[p.name for p in candidates]}"
    )
    skill_path = None
else:
    skill_path = candidates[0]
    if skill_path.name != "skill.md":
        # Two-step rename: a direct rename is a no-op on a case-insensitive FS.
        tmp = cli_dir / "skill.md.tmp-case"
        skill_path.rename(tmp)
        skill_path = cli_dir / "skill.md"
        tmp.rename(skill_path)
        print(f"Normalised skill file name -> {skill_path.name}")

if skill_path is not None:
    skill = skill_path.read_text()

    def require_skill_sub(old, new, label, *, expected=1, all_=False):
        global skill
        n = skill.count(old)
        if all_:
            if n < 1:
                failures.append(f"skill.md {label}: {old!r} not found")
                return
        elif n != expected:
            failures.append(
                f"skill.md {label}: expected {expected} occurrence(s) of {old!r}, found {n}. "
                "The generator template has changed -- update this script."
            )
            return
        skill = skill.replace(old, new)

    require_skill_sub('name: "localhost-cli"', 'name: "nocodb-cli"', "skill name")
    require_skill_sub(
        "CLI for the localhost MCP server",
        "CLI for the NocoDB MCP server",
        "description",
    )
    require_skill_sub("# localhost CLI", "# NocoDB CLI", "heading")
    require_skill_sub(
        "uv run --with fastmcp python generated.py",
        "nocodb",
        "invocation",
        all_=True,
    )

if failures:
    print("\nPost-processing FAILED -- nothing was written:", file=sys.stderr)
    for f in failures:
        print(f"  - {f}", file=sys.stderr)
    sys.exit(1)

path.write_text(content)
skill_path.write_text(skill)
print("Updated CLIENT_SPEC, imports, app name, docstring, skill.md")
EOF

# Final gate: the emitted command names must EXACTLY equal the server's tool
# names. Counts are not a check -- generated.py once carried 62 commands
# against a 62-tool server while two were ghosts and two were missing.
python3 << 'PYEOF'
import asyncio
import os
import re
import sys
from pathlib import Path

from fastmcp import Client

from nocodb.mcpserver.server import mcp

path = Path(os.environ["PROJECT_DIR"]) / "cli/generated.py"
generated = set(
    re.findall(r"@call_tool_app\.command\(name='([^']+)'", path.read_text())
)


async def main():
    async with Client(mcp) as client:
        return {tool.name for tool in await client.list_tools()}


live = asyncio.run(main())

ghosts = sorted(generated - live)
missing = sorted(live - generated)

if ghosts or missing:
    print("\nCLI/server name-set MISMATCH:", file=sys.stderr)
    print(f"  ghosts  (in CLI, not on server): {ghosts}", file=sys.stderr)
    print(f"  missing (on server, not in CLI): {missing}", file=sys.stderr)
    sys.exit(1)

print(f"CLI regenerated: {len(generated)} tool commands, name set matches server exactly")
PYEOF

echo ""
echo "Test with:"
echo "  python -m nocodb.cli --help"
echo "  nocodb tables list"
