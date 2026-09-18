"""Repo-wide pytest configuration.

Guarantees the repository root is on ``sys.path`` so ``nocodb`` and ``nocobot``
resolve to the working tree no matter which directory pytest is invoked from,
and disables FastMCP's camelCase compatibility bridge for the whole session.

This used to happen by accident. pytest prepends the rootdir for test files
that live in packages, so imports resolved even though the editable installs
were broken -- the ``nocodb`` finder pointed at a path that no longer exists,
and the ``nocobot`` editable install maps no modules at all (its pyproject sets
``packages = ["nocobot"]`` but sits inside the package directory, so hatchling
looks for ``nocobot/nocobot``). Relying on that was luck, not correctness.
Making the path explicit here means a test run from another cwd behaves the
same as one from the repo root.
"""

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Turn FastMCP's camelCase compatibility bridge off for the test session.
#
# FastMCP 4 is built on MCP Python SDK v2, which renamed every protocol model
# field camelCase -> snake_case. FastMCP ships shims so that legacy reads like
# `tool.inputSchema` keep working, emitting a FastMCPDeprecationWarning per
# read. That bridge is useful in production and actively harmful in a test
# suite: a read this migration failed to convert would warn and pass rather
# than fail, and the suite would report a clean migration it had not verified.
#
# Set before any fastmcp import: the setting is loaded from the environment
# when fastmcp's settings object is constructed at import time, though each
# shim consults it at read time thereafter. Nothing above imports fastmcp.
#
# `mcpserver_test.py` asserts this actually took effect. Without that check a
# renamed or mistyped variable would silently leave the bridge on, which is the
# same fail-open shape the setting exists to eliminate.
os.environ.setdefault("FASTMCP_MCP_CAMELCASE_COMPAT", "False")
