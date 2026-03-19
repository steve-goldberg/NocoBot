FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy project metadata first
COPY pyproject.toml LICENSE ./

# Copy all source files into nocobot/ subdirectory to match package structure
# (Docker context is nocobot/, so we recreate the package hierarchy)
COPY __init__.py __main__.py main.py agent.py mcp_client.py config.py ratelimit.py vision.py ./nocobot/
COPY bus/ ./nocobot/bus/
COPY channels/ ./nocobot/channels/
COPY providers/ ./nocobot/providers/

# Install the package
RUN uv pip install --system --no-cache .

# Run as non-root user
# --home is required: without it adduser defaults to /nonexistent,
# which breaks Python's Path.home() and causes permission errors for media downloads.
RUN addgroup --system app && adduser --system --home /home/app --ingroup app app
RUN mkdir -p /home/app/.nocobot && chown app:app /home/app/.nocobot
USER app

ENTRYPOINT ["nocobot"]
