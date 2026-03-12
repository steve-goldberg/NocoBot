FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy project metadata first
COPY pyproject.toml LICENSE ./

# Copy all source files into nocobot/ subdirectory to match package structure
# (Docker context is nocobot/, so we recreate the package hierarchy)
COPY __init__.py __main__.py main.py agent.py mcp_client.py config.py ratelimit.py ./nocobot/
COPY bus/ ./nocobot/bus/
COPY channels/ ./nocobot/channels/
COPY providers/ ./nocobot/providers/

# Install the package
RUN uv pip install --system --no-cache .

# Create config directory
RUN mkdir -p /root/.nocobot

ENTRYPOINT ["nocobot"]
