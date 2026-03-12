FROM python:3.12-slim

WORKDIR /app

# Upgrade pip and install uv for fast dependency installation
RUN pip install --upgrade pip && pip install uv

# Install the package with MCP dependencies
COPY . .
RUN uv pip install --system -e ".[mcp]"

# Default port
ENV MCP_PORT=8000
ENV MCP_HOST=0.0.0.0

EXPOSE 8000

# Run HTTP server
CMD ["python", "-m", "nocodb.mcpserver", "--http"]
