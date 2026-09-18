"""Tests for nocobot's MCP client.

The module had no coverage at all before the move to ``fastmcp.Client`` — the
agent tests substitute a bare ``AsyncMock`` — so these are the only tests
watching it.

The auth test deliberately drives a real HTTP server in a subprocess rather
than asserting on the client object. ``auth=<str>`` becomes a ``BearerAuth``
that sets the header inside ``auth_flow()`` at request time, so it never
appears on ``client.headers``: an assertion there would pass whether or not the
key was ever sent. ``asgi_server`` is no help either, since it has no socket
and ``MCPClient`` builds its own transport internally. The only honest check is
to ask a running server what it actually received.
"""

from __future__ import annotations

import pytest
from fastmcp import FastMCP
from fastmcp.client.transports import SSETransport, StreamableHttpTransport
from fastmcp.server.dependencies import get_http_headers
from fastmcp.utilities.tests import run_server_in_process

from nocobot.mcp_client import SESSION_TIMEOUT, MCPClient

API_KEY = "s3cret-probe-key"


def _build_probe_server() -> FastMCP:
    """A server that reports back what the transport actually delivered."""
    server = FastMCP("probe")

    @server.tool
    def echo_auth() -> str:
        """Return the Authorization header this request arrived with."""
        # get_http_headers() strips auth headers unless asked for them by name.
        headers = get_http_headers(include={"authorization"})
        return headers.get("authorization", "")

    @server.tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @server.tool
    def boom() -> str:
        """Always fail, to exercise the error path."""
        raise ValueError("deliberate probe failure")

    @server.resource("probe://greeting")
    def greeting() -> str:
        """A greeting."""
        return "hello from the probe resource"

    return server


def _run_probe_server(host: str, port: int) -> None:
    """Entry point for the server subprocess (must be importable at module level)."""
    _build_probe_server().run(transport="http", host=host, port=port)


@pytest.fixture(scope="module")
def probe_url():
    """A real probe server on a real port, shared by the tests that need one."""
    with run_server_in_process(_run_probe_server) as url:
        yield f"{url}/mcp"


# --- the acceptance gate -------------------------------------------------


async def test_authorization_header_reaches_the_server(probe_url):
    """The bearer token must arrive on the outbound request, not just be configured."""
    client = MCPClient(probe_url, api_key=API_KEY)
    try:
        await client.connect()
        received = await client.call_tool("echo_auth", {})
    finally:
        await client.close()

    assert received == f"Bearer {API_KEY}"


async def test_no_authorization_header_when_no_api_key(probe_url):
    """Without a key, nothing should be sent — the absence is the assertion."""
    client = MCPClient(probe_url, api_key=None)
    try:
        await client.connect()
        received = await client.call_tool("echo_auth", {})
    finally:
        await client.close()

    assert received == ""


# --- the timeout trap ----------------------------------------------------


def test_session_timeout_is_carried_onto_the_client():
    """Left to default this is 300s, which drops the long-lived stream."""
    client = MCPClient("http://example.invalid/mcp")._build_client()

    assert client._session_kwargs["read_timeout_seconds"] == float(SESSION_TIMEOUT)
    assert SESSION_TIMEOUT == 3600


# --- transport selection, which used to be a hand-written branch ---------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://example.invalid/mcp", StreamableHttpTransport),
        ("http://example.invalid/sse", SSETransport),
        ("http://example.invalid/sse/", SSETransport),
    ],
)
def test_transport_is_inferred_from_the_url(url, expected):
    """The deleted _is_sse branch is redundant, not silently dropped."""
    assert isinstance(MCPClient(url)._build_client().transport, expected)


# --- discovery -----------------------------------------------------------


async def test_discover_reads_tool_schemas_and_resources(probe_url):
    client = MCPClient(probe_url)
    try:
        await client.connect()
        tools = client.get_tools_for_llm()
        resource = client.get_resource("probe://greeting")
    finally:
        await client.close()

    add = next(t for t in tools if t["function"]["name"] == "add")
    # A real schema, not the {} the old hasattr fallback would have shipped.
    assert set(add["function"]["parameters"]["properties"]) == {"a", "b"}
    assert resource == "hello from the probe resource"


async def test_discover_raises_when_a_tool_has_no_schema():
    """The old fallback masked this as {}; a missing schema must now be loud."""

    class _SchemalessTool:
        name = "broken"
        description = "no schema"

    class _FakeClient:
        async def list_tools(self):
            return [_SchemalessTool()]

        async def list_resources(self):  # pragma: no cover - never reached
            return []

    with pytest.raises(AttributeError):
        await MCPClient("http://example.invalid/mcp")._discover(_FakeClient())


# --- error path ----------------------------------------------------------


async def test_failing_tool_is_reported_as_a_tool_error(probe_url):
    """raise_on_error=False keeps this on the is_error branch, not the except."""
    client = MCPClient(probe_url)
    try:
        await client.connect()
        result = await client.call_tool("boom", {})
    finally:
        await client.close()

    # The generic handler would say "Tool call failed"; this must not.
    assert result == "Tool returned an error. Please try a different approach."
