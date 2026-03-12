"""MCP client for connecting to NocoDB MCP server via HTTP streamable transport."""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from typing import Any

from loguru import logger
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client


class MCPClient:
    """Client for NocoDB MCP server using HTTP streamable transport.

    Maintains a persistent MCP session via AsyncExitStack, reconnecting
    lazily if the session dies (e.g. server restart).
    """

    def __init__(self, url: str, tool_timeout: int = 30):
        """Initialize MCP client.

        Args:
            url: MCP server URL (e.g., http://ncdbmcp.lab/mcp)
            tool_timeout: Timeout in seconds for individual tool calls
        """
        self.url = url
        self._tool_timeout = tool_timeout
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._connected: bool = False
        self._lock = asyncio.Lock()
        self._tools: list[dict[str, Any]] = []
        self._resources: dict[str, str] = {}

    @property
    def _is_sse(self) -> bool:
        """Whether the URL indicates SSE transport."""
        return self.url.rstrip("/").endswith("/sse")

    def _open_transport(self):
        """Create the appropriate transport context manager."""
        if self._is_sse:
            return sse_client(self.url, timeout=3600)
        return streamablehttp_client(self.url, timeout=3600)

    async def _ensure_session(self) -> ClientSession:
        """Return the persistent session, reconnecting if needed."""
        if self._session is not None and self._connected:
            return self._session
        async with self._lock:
            # Double-check after acquiring lock
            if self._session is not None and self._connected:
                return self._session
            await self._close()
            stack = AsyncExitStack()
            await stack.__aenter__()
            try:
                transport = await stack.enter_async_context(self._open_transport())
                read, write = transport[0], transport[1]
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
            except BaseException:
                await stack.aclose()
                raise
            self._stack = stack
            self._session = session
            self._connected = True
            logger.info("MCP session established to {}", self.url)
            return session

    async def _close(self) -> None:
        """Tear down the current session and stack."""
        if self._stack:
            try:
                await self._stack.aclose()
            except (RuntimeError, BaseExceptionGroup):
                pass  # MCP SDK cancel scope cleanup noise
            self._stack = None
        self._session = None
        self._connected = False

    async def close(self) -> None:
        """Public cleanup — call during bot shutdown."""
        await self._close()

    async def connect(self) -> None:
        """Connect to the MCP server and discover tools/resources."""
        logger.info("Connecting to MCP server at {}...", self.url)

        session = await self._ensure_session()

        # Discover tools
        tools_result = await session.list_tools()
        self._tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                }
            }
            for tool in tools_result.tools
        ]
        logger.info("Discovered {} MCP tools", len(self._tools))

        # Discover and cache resources
        resources_result = await session.list_resources()
        for resource in resources_result.resources:
            content = await session.read_resource(resource.uri)
            if content.contents:
                self._resources[str(resource.uri)] = content.contents[0].text
        logger.info("Cached {} MCP resources", len(self._resources))

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call an MCP tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result as string
        """
        try:
            session = await self._ensure_session()
            result = await asyncio.wait_for(
                session.call_tool(name, arguments),
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

        if result.isError:
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
        workflow = self.get_resource("nocodb://workflow-guide")
        reference = self.get_resource("nocodb://reference")

        parts = [
            "You are nocobot, a helpful assistant for working with NocoDB databases.",
            "You have access to NocoDB tools via MCP to help users manage their data.",
            "",
        ]

        if workflow:
            parts.append(workflow)
            parts.append("")

        if reference:
            parts.append(reference)

        return "\n".join(parts)
