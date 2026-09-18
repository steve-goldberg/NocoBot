FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Dependencies come from requirements-mcp.txt, which is fully pinned. This
# build previously ran `uv pip install --system -e ".[mcp]"`, resolving against
# live PyPI on every build: with auto-deploy-on-push configured, an unrelated
# edit could ship a new major version of FastMCP to production without anyone
# choosing to upgrade.
#
# Regenerate after any dependency change in setup.py:
#   uv pip compile setup.py --extra mcp \
#       --python-version 3.12 --python-platform linux -o requirements-mcp.txt
# The flags matter: resolve for the image's interpreter and platform, not the
# machine that happens to run the command.
#
# Copied before the source so an edit to the code -- or to docs/ -- reuses this
# layer instead of reinstalling the whole dependency tree.
COPY requirements-mcp.txt ./
RUN uv pip install --system --no-cache -r requirements-mcp.txt

# Build context is nocodb/, and must stay that way: setup.py maps package_dir
# onto '.' and reads README.md from the working directory.
COPY . .

# --no-deps keeps the resolver from re-widening what the lockfile just pinned.
RUN uv pip install --system --no-cache --no-deps .

# Fail the build if setup.py and requirements-mcp.txt have drifted apart.
#
# nocobot/Dockerfile gets this from `uv export --locked`, which has no
# equivalent for a setup.py project (uv pip compile has no --check). This is
# the same guarantee by another route: re-resolve the declared dependencies
# with the network disabled, so the build can only succeed if every specifier
# in setup.py is already satisfied by what requirements-mcp.txt installed.
# Bump a floor without recompiling and this exits non-zero here, rather than
# shipping an image whose contents no longer match its manifest.
#
# setuptools is needed to read setup.py's metadata and is not in the runtime
# tree, so it is installed, used, and removed within this one layer.
# --no-build-isolation makes the metadata build use it instead of trying to
# fetch its own copy, which --offline would refuse.
RUN uv pip install --system --no-cache setuptools \
 && uv pip install --system --offline --no-build-isolation --dry-run ".[mcp]" > /dev/null \
 && uv pip uninstall --system setuptools

# Default port
ENV MCP_PORT=8000
ENV MCP_HOST=0.0.0.0

EXPOSE 8000

# Run HTTP server
CMD ["python", "-m", "nocodb.mcpserver", "--http"]
