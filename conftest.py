"""Repo-wide pytest configuration.

Guarantees the repository root is on ``sys.path`` so ``nocodb`` and ``nocobot``
resolve to the working tree no matter which directory pytest is invoked from.

This used to happen by accident. pytest prepends the rootdir for test files
that live in packages, so imports resolved even though the editable installs
were broken -- the ``nocodb`` finder pointed at a path that no longer exists,
and the ``nocobot`` editable install maps no modules at all (its pyproject sets
``packages = ["nocobot"]`` but sits inside the package directory, so hatchling
looks for ``nocobot/nocobot``). Relying on that was luck, not correctness.
Making the path explicit here means a test run from another cwd behaves the
same as one from the repo root.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
