"""MCP client for connecting to NocoDB MCP server via HTTP streamable transport."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client


class MCPClient:
    """Client for NocoDB MCP server using HTTP streamable transport."""

    def __init__(self, url: str, tool_timeout: int = 30):
        """Initialize MCP client.

        Args:
            url: MCP server URL (e.g., http://ncdbmcp.lab/mcp)
            tool_timeout: Timeout in seconds for individual tool calls
        """
        self.url = url
        self._tool_timeout = tool_timeout
        self._session: ClientSession | None = None
        self._tools: list[dict[str, Any]] = []
        self._resources: dict[str, str] = {}

    @property
    def _is_sse(self) -> bool:
        """Whether the URL indicates SSE transport."""
        return self.url.rstrip("/").endswith("/sse")

    async def connect(self) -> None:
        """Connect to the MCP server and discover tools/resources."""
        logger.info(f"Connecting to MCP server at {self.url}...")

        transport_cm = (
            sse_client(self.url, timeout=3600)
            if self._is_sse
            else streamablehttp_client(self.url, timeout=3600)
        )
        async with transport_cm as transport:
            read, write = transport[0], transport[1]
            async with ClientSession(read, write) as session:
                self._session = session
                await session.initialize()

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
                logger.info(f"Discovered {len(self._tools)} MCP tools")

                # Discover and cache resources
                resources_result = await session.list_resources()
                for resource in resources_result.resources:
                    content = await session.read_resource(resource.uri)
                    if content.contents:
                        self._resources[str(resource.uri)] = content.contents[0].text
                logger.info(f"Cached {len(self._resources)} MCP resources")

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call an MCP tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result as string
        """
        transport_cm = (
            sse_client(self.url, timeout=3600)
            if self._is_sse
            else streamablehttp_client(self.url, timeout=3600)
        )
        async with transport_cm as transport:
            read, write = transport[0], transport[1]
            async with ClientSession(read, write) as session:
                await session.initialize()

                try:
                    result = await asyncio.wait_for(
                        session.call_tool(name, arguments),
                        timeout=self._tool_timeout,
                    )
                except asyncio.TimeoutError:
                    logger.warning("MCP tool '{}' timed out after {}s", name, self._tool_timeout)
                    return f"(MCP tool call timed out after {self._tool_timeout}s)"
                except asyncio.CancelledError:
                    task = asyncio.current_task()
                    if task is not None and task.cancelling() > 0:
                        raise
                    logger.warning("MCP tool '{}' was cancelled by server/SDK", name)
                    return "(MCP tool call was cancelled)"
                except Exception as exc:
                    logger.exception("MCP tool '{}' failed: {}: {}", name, type(exc).__name__, exc)
                    return f"(MCP tool call failed: {type(exc).__name__})"

                # Extract text content from result
                if result.content:
                    texts = [c.text for c in result.content if hasattr(c, 'text')]
                    return "\n".join(texts)
                return ""

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
