"""MCP client for connecting to the NocoDB MCP server via fastmcp's Client."""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from typing import Any

from fastmcp import Client
from loguru import logger

# Read timeout for the long-lived MCP stream. Left to default, the transport
# falls back to a 300s read timeout, which silently drops the stream on an idle
# bot — reconnect churn with no error at the call site.
SESSION_TIMEOUT = 3600


class MCPClient:
    """Client for the NocoDB MCP server, built on fastmcp's own Client.

    Maintains a persistent MCP session via AsyncExitStack, reconnecting
    lazily if the session dies (e.g. server restart).
    """

    def __init__(self, url: str, tool_timeout: int = 30, api_key: str | None = None):
        """Initialize MCP client.

        Args:
            url: MCP server URL (e.g., http://localhost:8000/mcp)
            tool_timeout: Timeout in seconds for individual tool calls
            api_key: Optional API key for MCP server authentication
        """
        self.url = url
        self._tool_timeout = tool_timeout
        self._api_key = api_key
        self._stack: AsyncExitStack | None = None
        self._client: Client | None = None
        self._connected: bool = False
        self._lock = asyncio.Lock()
        self._tools: list[dict[str, Any]] = []
        self._resources: dict[str, str] = {}

    def _build_client(self) -> Client:
        """Create a Client for the configured URL.

        Transport is inferred from the URL — ``/mcp`` gives Streamable HTTP and
        ``/sse`` gives SSE — and ``auth`` is formatted into the
        ``Authorization: Bearer`` header for us.
        """
        return Client(self.url, auth=self._api_key, timeout=SESSION_TIMEOUT)

    async def _ensure_session(self) -> Client:
        """Return the persistent client, reconnecting and re-discovering tools if needed."""
        if self._client is not None and self._connected:
            return self._client
        async with self._lock:
            # Double-check after acquiring lock
            if self._client is not None and self._connected:
                return self._client
            reconnecting = self._tools != []  # Had tools before → reconnect
            await self._close()
            stack = AsyncExitStack()
            await stack.__aenter__()
            try:
                client = await stack.enter_async_context(self._build_client())
            except BaseException:
                await stack.aclose()
                raise
            self._stack = stack
            self._client = client
            self._connected = True
            logger.info("MCP session established to {}", self.url)
            if reconnecting:
                await self._discover(client)
            return client

    async def _close(self) -> None:
        """Tear down the current session and stack."""
        if self._stack:
            try:
                await self._stack.aclose()
            except (RuntimeError, BaseExceptionGroup):
                pass  # MCP SDK cancel scope cleanup noise
            self._stack = None
        self._client = None
        self._connected = False

    async def close(self) -> None:
        """Public cleanup — call during bot shutdown."""
        await self._close()

    async def _discover(self, client: Client) -> None:
        """Discover and cache tools and resources from the MCP server."""
        tools = await client.list_tools()
        self._tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                }
            }
            for tool in tools
        ]
        logger.info("Discovered {} MCP tools", len(self._tools))

        resources = await client.list_resources()
        self._resources = {}
        for resource in resources:
            contents = await client.read_resource(resource.uri)
            if contents:
                self._resources[str(resource.uri)] = contents[0].text
        logger.info("Cached {} MCP resources", len(self._resources))

    async def connect(self) -> None:
        """Connect to the MCP server and discover tools/resources."""
        logger.info("Connecting to MCP server at {}...", self.url)
        client = await self._ensure_session()
        await self._discover(client)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call an MCP tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result as string
        """
        try:
            client = await self._ensure_session()
            # raise_on_error=False keeps a failing tool as a returned result, so
            # the error text below still reaches the log. Left to default, it
            # would raise and be swallowed by the generic handler.
            result = await asyncio.wait_for(
                client.call_tool(name, arguments, raise_on_error=False),
                timeout=self._tool_timeout,
            )
        except asyncio.TimeoutError:
            self._connected = False
            logger.warning("MCP tool '{}' timed out after {}s", name, self._tool_timeout)
            return "Tool timed out. Please try a simpler request."
        except asyncio.CancelledError:
            task = asyncio.current_task()
            if task is not None and task.cancelling() > 0:
                raise
            self._connected = False
            logger.warning("MCP tool '{}' was cancelled by server/SDK", name)
            return "Tool call was cancelled."
        except Exception as exc:
            self._connected = False
            logger.exception("MCP tool '{}' failed: {}: {}", name, type(exc).__name__, exc)
            return "Tool call failed. Please try a different approach."

        # Extract text content from result
        text = ""
        if result.content:
            texts = [c.text for c in result.content if hasattr(c, 'text')]
            text = "\n".join(texts)

        if result.is_error:
            logger.warning("MCP tool '{}' returned error: {}", name, text)
            return "Tool returned an error. Please try a different approach."

        return text

    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """Get tools in OpenAI function-calling format."""
        return self._tools

    def get_resource(self, uri: str) -> str:
        """Get cached resource content.

        Args:
            uri: Resource URI (e.g., nocodb://workflow-guide)

        Returns:
            Resource content as string
        """
        return self._resources.get(uri, "")

    def get_system_prompt(self) -> str:
        """Build system prompt from MCP resources."""
        workflow = self.get_resource("nocodb://schema-discovery-rules")
        reference = self.get_resource("nocodb://tools-reference")

        parts = [
            "You are NocoBot, a Telegram assistant that manages NocoDB databases.",
            "You talk to users via Telegram and execute operations through MCP tools.",
            "",
            "## Identity",
            "- You are confident and direct. If a tool exists for something, you use it.",
            "- You speak concisely — Telegram messages should be short and scannable.",
            "- You use plain language, not API jargon. Say 'table' not 'tableId'.",
            "- When you complete an action, confirm what you did with specifics (names, counts).",
            "",
            "## Capabilities — What You CAN Do",
            "- **Full CRUD** on tables, fields, records, links, views, filters, sorts, members",
            "- **Create any field type** including Links (relationships between tables)",
            "- **Create Links fields** with `field_create` using type 'Links' and options",
            '  `{"relation_type": "hm"|"bt"|"mm", "related_table_id": "tbl_xxx"}`',
            "- **Link/unlink records** across related tables",
            "- **Export CSV**, upload attachments, manage shared views",
            "- **Batch operations** — create/update/delete multiple records at once",
            "",
            "## Capabilities — What You CANNOT Do (self-hosted limitations)",
            "- Cannot create bases (list only)",
            "- Cannot create views (list/update/delete only)",
            "- Cannot create/update webhooks (list/delete only)",
            "- Cannot trigger button actions",
            "",
            "Do NOT claim other limitations. If you're unsure whether you can do something,",
            "try it. The tool will tell you if it fails.",
            "",
            "## Reference Tools (call on-demand via read_resource)",
            "- `nocodb://schema-discovery-rules` — CALL FIRST before any query",
            "- `nocodb://tools-reference` — Tool reference by category, field types, filter syntax",
            "- `nocodb://formula-reference` — Formula functions and operators",
            "",
            "## Rules",
            "1. **Always discover schema first** — call `fields_list` before using sort/where",
            "2. **Field names are case-sensitive** — never guess, always look up",
            "3. **Destructive operations need confirm=True** — always ask the user first",
            "4. **Don't leak internals** — never show raw error details, URLs, or field IDs",
            "   to the user unless they ask",
            "5. **If a tool fails, try a different approach** — don't repeat the same call",
            "6. **Keep responses short** — Telegram isn't a document viewer",
            "",
        ]

        if workflow:
            parts.append(workflow)
            parts.append("")

        if reference:
            parts.append(reference)

        return "\n".join(parts)
