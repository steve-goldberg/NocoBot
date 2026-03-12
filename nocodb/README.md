<h1 align="center">nocodb-py</h1>

<h2 align="center"><strong>The Complete Python Toolkit for NocoDB</strong></h2>

<p align="center">
  <a href="https://www.gnu.org/licenses/agpl-3.0"><img src="https://img.shields.io/badge/License-AGPL--3.0-blue.svg" alt="License: AGPL-3.0"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
</p>

<p align="center">Python SDK + MCP Server + CLI for <b>self-hosted</b> NocoDB.</p>

---

## 📰 News

- **2026-02-13** ⌨️ Auto-generated CLI via FastMCP generate-cli
- **2026-02-12** 📚 Doc tools for mcp-remote compatibility
- **2026-02-11** 🚀 FastMCP 3.0 upgrade with Streamable HTTP transport
- **2026-02-11** 📦 Schema export tools and workflow prompts
- **2026-02-11** 🐳 Dokploy deployment guide for remote MCP
- **2026-01-26** 🎉 MCP server with 62 tools exposing full SDK

---

## Key Features

- 🐍 **Python SDK** - Full v3 Data API + hybrid v2/v3 Meta API
- 🤖 **MCP Server** - 62 tools for Claude Desktop & AI integrations (FastMCP 3.0)
- ⌨️ **CLI** - 62 commands auto-generated from MCP server
- 🏠 **Self-Hosted First** - Built for community edition

---

![Architecture](docs/architecture.png)

---

## Quick Start

### 1. Install

```bash
# SDK only
pip install git+https://github.com/steve-goldberg/nocodb-py.git

# With CLI + MCP server
pip install "nocodb-py[cli,mcp] @ git+https://github.com/steve-goldberg/nocodb-py.git"
```

### 2. Configure

```bash
export NOCODB_URL="http://localhost:8080"
export NOCODB_TOKEN="your-api-token"
```

### 3. Use

```bash
# CLI
nocodb records list BASE_ID TABLE_ID

# Python
from nocodb import APIToken
from nocodb.infra.requests_client import NocoDBRequestsClient

client = NocoDBRequestsClient(APIToken("your-token"), "http://localhost:8080")
records = client.records_list_v3(base_id, table_id)
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [SDK](docs/SDK.md) | Python client API reference |
| [CLI](docs/CLI.md) | Command-line interface usage |
| [MCP Server](docs/MCP.md) | AI assistant integration |
| [Filters](docs/FILTERS.md) | Query filter system |
| [Deployment](docs/DOKPLOY_DEPLOYMENT.md) | Docker/Dokploy deployment |

---

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

## License

AGPL-3.0

Based on [nocodb-python-client](https://github.com/ElChicoDePython/python-nocodb) by Samuel Lopez Saura (MIT 2022).
