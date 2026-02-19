#!/bin/bash
# Regenerate the CLI from the MCP server.
#
# Run this script after modifying MCP tools in nocodb/mcp/tools/.
# It starts the MCP server temporarily and generates a new CLI from its schema.
#
# Usage:
#   ./scripts/regenerate-cli.sh
#
# Requirements:
#   - fastmcp >= 3.0.0
#   - NOCODB_URL, NOCODB_TOKEN, NOCODB_BASE_ID environment variables (or test values)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Use test values if not set (the server needs these to start, but won't actually connect)
export NOCODB_URL="${NOCODB_URL:-http://localhost:8080}"
export NOCODB_TOKEN="${NOCODB_TOKEN:-test_token}"
export NOCODB_BASE_ID="${NOCODB_BASE_ID:-test_base}"

# Find an available port
PORT=9876
while nc -z localhost $PORT 2>/dev/null; do
    PORT=$((PORT + 1))
done

echo "Starting MCP server on port $PORT..."

# Start the MCP server in the background
python -m nocodb.mcpserver --http --port $PORT &
SERVER_PID=$!

# Wait for server to be ready
sleep 3

# Verify server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Error: MCP server failed to start"
    exit 1
fi

echo "Generating CLI from MCP server..."

# Generate the CLI
if fastmcp generate-cli "http://localhost:$PORT/mcp" nocodb/cli/generated.py -f --timeout 60; then
    echo "✓ Generated nocodb/cli/generated.py"
else
    echo "Error: Failed to generate CLI"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Kill the server
kill $SERVER_PID 2>/dev/null || true

# Post-process: Update CLIENT_SPEC to use StdioTransport
# The generated file points to the HTTP URL, we need to change it to stdio
python3 << 'EOF'
import re

with open("nocodb/cli/generated.py", "r") as f:
    content = f.read()

# Replace the CLIENT_SPEC line
old_spec = re.search(r"CLIENT_SPEC = 'http://localhost:\d+/mcp'", content)
if old_spec:
    content = content.replace(
        old_spec.group(0),
        '''CLIENT_SPEC = StdioTransport(
    command=sys.executable,
    args=["-m", "nocodb.mcpserver"],
)'''
    )

# Add StdioTransport import if not present
if "from fastmcp.client.transports import StdioTransport" not in content:
    content = content.replace(
        "from fastmcp import Client",
        "from fastmcp import Client\nfrom fastmcp.client.transports import StdioTransport"
    )

# Update app name and help
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

with open("nocodb/cli/generated.py", "w") as f:
    f.write(content)

print("✓ Updated CLIENT_SPEC to use StdioTransport")
print("✓ Updated app name to 'nocodb'")
EOF

# Also update SKILL.md naming
if [ -f "nocodb/cli/SKILL.md" ]; then
    sed -i '' 's/name: "localhost-cli"/name: "nocodb-cli"/' nocodb/cli/SKILL.md
    sed -i '' 's/CLI for the localhost MCP server/CLI for the NocoDB MCP server/' nocodb/cli/SKILL.md
    sed -i '' 's/# localhost CLI/# NocoDB CLI/' nocodb/cli/SKILL.md
    sed -i '' 's|uv run --with fastmcp python generated.py|nocodb|g' nocodb/cli/SKILL.md
    echo "✓ Updated SKILL.md naming"
fi

echo ""
echo "CLI regenerated successfully!"
echo ""
echo "Files updated:"
echo "  - nocodb/cli/generated.py (62 tool commands)"
echo "  - nocodb/cli/SKILL.md (agent skill documentation)"
echo ""
echo "Test with:"
echo "  python -m nocodb.cli --help"
echo "  nocodb tables list"
