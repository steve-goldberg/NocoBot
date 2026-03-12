#!/bin/bash
# Regenerate the CLI from the MCP server using fastmcp generate-cli.
#
# Usage:
#   ./scripts/regenerate-cli.sh
#
# Requirements:
#   - fastmcp >= 3.0.0
#   - NOCODB_URL, NOCODB_TOKEN, NOCODB_BASE_ID (via .env, env vars, or .nocodbrc)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$PROJECT_DIR")"

# Source .env if it exists
if [ -f "$REPO_ROOT/.env" ]; then
    source "$REPO_ROOT/.env"
fi

# Find an available port
PORT=9876
while nc -z localhost $PORT 2>/dev/null; do
    PORT=$((PORT + 1))
done

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
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

kill $SERVER_PID 2>/dev/null || true

# Post-process: CLIENT_SPEC -> StdioTransport, app name -> nocodb
python3 << 'EOF'
import re, sys, os

path = os.path.join(os.environ.get("PROJECT_DIR", ""), "cli/generated.py")
if not os.path.exists(path):
    # fallback
    path = sys.argv[1] if len(sys.argv) > 1 else "cli/generated.py"

with open(path, "r") as f:
    content = f.read()

# Replace CLIENT_SPEC from HTTP URL to StdioTransport
old_spec = re.search(r"CLIENT_SPEC = 'http://localhost:\d+/mcp'", content)
if old_spec:
    content = content.replace(
        old_spec.group(0),
        "CLIENT_SPEC = StdioTransport(\n"
        "    command=sys.executable,\n"
        '    args=["-m", "nocodb.mcpserver"],\n'
        "    env=os.environ.copy(),\n"
        ")"
    )

# Add StdioTransport and os imports
if "from fastmcp.client.transports import StdioTransport" not in content:
    content = content.replace(
        "from fastmcp import Client",
        "from fastmcp import Client\nfrom fastmcp.client.transports import StdioTransport"
    )
if "import os" not in content:
    content = content.replace(
        "import sys",
        "import os\nimport sys"
    )

# Update app name
content = re.sub(
    r'app = cyclopts\.App\(name="localhost", help="CLI for localhost MCP server"\)',
    'app = cyclopts.App(name="nocodb", help="NocoDB CLI - Agent-friendly command-line interface")',
    content
)

# Update docstring
content = re.sub(
    r'"""CLI for localhost MCP server\.',
    '"""CLI for NocoDB MCP server.',
    content
)

with open(path, "w") as f:
    f.write(content)

print("Updated CLIENT_SPEC, app name, docstring")
EOF

# Update SKILL.md naming
if [ -f "$PROJECT_DIR/cli/SKILL.md" ]; then
    sed -i '' 's/name: "localhost-cli"/name: "nocodb-cli"/' "$PROJECT_DIR/cli/SKILL.md"
    sed -i '' 's/CLI for the localhost MCP server/CLI for the NocoDB MCP server/' "$PROJECT_DIR/cli/SKILL.md"
    sed -i '' 's/# localhost CLI/# NocoDB CLI/' "$PROJECT_DIR/cli/SKILL.md"
    sed -i '' "s|uv run --with fastmcp python generated.py|nocodb|g" "$PROJECT_DIR/cli/SKILL.md"
    echo "Updated SKILL.md"
fi

export PROJECT_DIR="$PROJECT_DIR"
python3 << 'PYEOF'
import os
path = os.path.join(os.environ["PROJECT_DIR"], "cli/generated.py")
with open(path, "r") as f:
    content = f.read()

import re
# Count tools
tools = re.findall(r'@call_tool_app\.command', content)
print(f"CLI regenerated: {len(tools)} tool commands")
PYEOF

echo ""
echo "Test with:"
echo "  python -m nocodb.cli --help"
echo "  nocodb tables list"
