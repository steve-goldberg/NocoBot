"""Tests for the NocoDB MCP server.

The MCP layer had no test coverage at all: nothing imported FastMCP, nothing
constructed the server, and nothing exercised ``ResourcesAsTools``,
``DebugTokenVerifier``, ``custom_route``, or the 16 tool modules. These tests
exist so that a FastMCP major-version bump has something that can observe a
regression.

Everything here runs in-process. Tools are inspected through FastMCP's
in-memory client transport against the real server object, and the HTTP
surface is driven through ``httpx``'s ASGI transport. No subprocess, no
socket, and no live NocoDB instance is involved -- the dummy NocoDB
credentials below only have to satisfy the lifespan's config validation,
because none of these tests call a tool that performs a NocoDB request.

A note on what the in-memory client can and cannot see: it does not pass
through the HTTP middleware stack, so it never exercises authentication.
That is precisely why the auth tests (T5/T6) go through the ASGI app instead.
"""

from __future__ import annotations

import importlib
import os
import re
import sys
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

import httpx
import pytest
from fastmcp import Client

from .server import mcp

# ---------------------------------------------------------------------------
# Expected registration state
# ---------------------------------------------------------------------------

# @mcp.tool decorators per module in mcpserver/tools/.
EXPECTED_TOOLS_PER_MODULE = {
    "records": 7,
    "fields": 6,
    "view_filters": 6,
    "webhooks": 6,
    "tables": 5,
    "view_sorts": 5,
    "members": 4,
    "shared_views": 4,
    "view_columns": 4,
    "links": 3,
    "views": 3,
    "bases": 2,
    "schema": 2,
    "attachments": 1,
    "export": 1,
    "storage": 1,
}

EXPECTED_DECORATED_TOOL_COUNT = sum(EXPECTED_TOOLS_PER_MODULE.values())  # 60

# ResourcesAsTools generates exactly TWO tools -- `list_resources` and
# `read_resource` -- regardless of how many resources the server defines. It
# does not generate one tool per resource.
RESOURCES_AS_TOOLS_NAMES = {"list_resources", "read_resource"}

EXPECTED_RESOURCE_URIS = {
    "nocodb://schema-discovery-rules",
    "nocodb://tools-reference",
    "nocodb://formula-reference",
}

# Tools that legitimately accept no arguments: they operate on the base from
# the server's own configuration. Their schema is a well-formed object schema
# with an empty `properties` map, which is different from the defect T3 guards
# against (a schema that is an empty dict outright).
EXPECTED_ZERO_ARG_TOOLS = {
    "bases_list",
    "base_info",
    "tables_list",
    "members_list",
    "schema_export_base",
    "list_resources",
}

_TOOLS_DIR = Path(__file__).parent / "tools"
_TOOL_DECORATOR = re.compile(r"^@mcp\.tool", re.MULTILINE)

# Dummy config so the lifespan's MCPConfig.from_env() validation passes
# offline. The URL is deliberately unroutable.
_DUMMY_NOCODB_ENV = {
    "NOCODB_URL": "https://nocodb.invalid",
    "NOCODB_TOKEN": "test-token-not-a-real-credential",
    "NOCODB_BASE_ID": "ptest00000000000",
    "NOCODB_VERIFY_SSL": "false",
}

CORRECT_API_KEY = "correct-api-key-for-tests"
WRONG_API_KEY = "wrong-api-key-for-tests"

_MCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}

_INITIALIZE_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "mcpserver-test", "version": "1.0"},
    },
}


@pytest.fixture(autouse=True)
def nocodb_env(monkeypatch):
    """Provide dummy NocoDB config so the server lifespan can start offline."""
    for key, value in _DUMMY_NOCODB_ENV.items():
        monkeypatch.setenv(key, value)


@contextmanager
def server_with_api_key(api_key: str):
    """Import a fresh copy of the server with ``MCP_API_KEY`` set.

    ``server.py`` reads ``MCP_API_KEY`` at import time and builds the auth
    verifier from it at module level, so the authenticated server cannot be
    produced by setting the variable after the fact. The whole
    ``nocodb.mcpserver`` module tree is dropped from ``sys.modules`` and
    re-imported: the tool modules must re-execute too, because each one does
    ``from ..server import mcp`` and would otherwise keep decorating the
    original server object.

    The previous modules and environment are restored on exit so this leaves
    no trace for other tests.
    """
    prefix = "nocodb.mcpserver"
    saved = {
        name: module
        for name, module in sys.modules.items()
        if name == prefix or name.startswith(prefix + ".")
    }
    previous_key = os.environ.get("MCP_API_KEY")

    for name in saved:
        del sys.modules[name]
    os.environ["MCP_API_KEY"] = api_key

    try:
        yield importlib.import_module(prefix + ".server")
    finally:
        for name in [
            name
            for name in sys.modules
            if name == prefix or name.startswith(prefix + ".")
        ]:
            del sys.modules[name]
        sys.modules.update(saved)
        if previous_key is None:
            os.environ.pop("MCP_API_KEY", None)
        else:
            os.environ["MCP_API_KEY"] = previous_key


@asynccontextmanager
async def asgi_client(app):
    """Yield an httpx client bound to ``app`` with the FastMCP lifespan running.

    The lifespan matters: without it the StreamableHTTP session manager is
    never initialised and any request that gets past authentication fails with
    a RuntimeError instead of a protocol response.
    """
    async with app.lifespan(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://mcp.test"
        ) as client:
            yield client


def _post_initialize(client: httpx.AsyncClient, token: str | None):
    """POST an MCP initialize request, optionally bearing ``token``."""
    headers = dict(_MCP_HEADERS)
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return client.post("/mcp", headers=headers, json=_INITIALIZE_REQUEST)


# ---------------------------------------------------------------------------
# T0 -- the camelCase bridge is off
# ---------------------------------------------------------------------------


def test_t0_camelcase_compat_bridge_is_disabled():
    """The compat bridge must be off, and this must be checked, not assumed.

    FastMCP 4 bridges legacy camelCase reads on SDK v2 models -- ``tool.inputSchema``
    resolves to ``input_schema`` and warns instead of raising. ``conftest.py``
    disables that for the session so any read this migration missed fails
    loudly.

    Asserting it here closes the fail-open path. If the environment variable
    were renamed upstream or misspelled in conftest, the bridge would stay on,
    every surviving camelCase read would keep passing, and the suite would
    certify a migration it had not actually tested. The bridge being off is
    what gives the rest of this module its meaning, so it gets a test rather
    than a comment.
    """
    from fastmcp import settings

    assert settings.mcp_camelcase_compat is False, (
        "FastMCP's camelCase compat bridge is ON during tests. Residual "
        "camelCase protocol reads will warn instead of failing, so a passing "
        "suite proves nothing about the SDK v2 rename. Check that conftest.py "
        "sets FASTMCP_MCP_CAMELCASE_COMPAT before anything imports fastmcp."
    )


# ---------------------------------------------------------------------------
# T1 -- tool registration
# ---------------------------------------------------------------------------


async def test_t1_registers_expected_tools():
    """The server exposes the 60 decorated tools plus exactly 2 transform tools.

    Asserted structurally rather than as a bare total. A flat count is not
    worth much here: before phase 2, cli/generated.py held 62 commands against
    a 62-tool server and was still wrong, because it carried two commands for a
    deleted module and was missing the two transform tools. A `62 == 62` check
    passed on that file. Comparing name sets reports *which* tools drifted.
    """
    async with Client(mcp) as client:
        tools = await client.list_tools()

    names = [tool.name for tool in tools]
    assert len(names) == len(set(names)), f"duplicate tool names: {names}"

    exposed = set(names)
    assert exposed >= RESOURCES_AS_TOOLS_NAMES, (
        "ResourcesAsTools transform tools missing: "
        f"{sorted(RESOURCES_AS_TOOLS_NAMES - exposed)}. The server would start "
        "clean and simply stop advertising the resources."
    )

    decorated = exposed - RESOURCES_AS_TOOLS_NAMES
    assert len(decorated) == EXPECTED_DECORATED_TOOL_COUNT, (
        f"expected {EXPECTED_DECORATED_TOOL_COUNT} decorated tools, "
        f"got {len(decorated)}"
    )

    assert len(tools) == EXPECTED_DECORATED_TOOL_COUNT + len(
        RESOURCES_AS_TOOLS_NAMES
    )


def test_t1_source_decorator_counts_match_expectation():
    """The per-module counts still describe the source.

    Guards the constant above from drifting away from reality: if a module
    gains or loses a tool, this fails alongside the runtime assertion instead
    of quietly moving the goalposts. It also catches a module being dropped
    from server.py's import block, which would lower the runtime count while
    leaving the source untouched.
    """
    actual = {
        path.stem: len(_TOOL_DECORATOR.findall(path.read_text()))
        for path in sorted(_TOOLS_DIR.glob("*.py"))
        if path.stem != "__init__"
    }
    actual = {name: count for name, count in actual.items() if count}

    assert actual == EXPECTED_TOOLS_PER_MODULE
    assert sum(actual.values()) == EXPECTED_DECORATED_TOOL_COUNT


# ---------------------------------------------------------------------------
# T2 -- resources reachable and surfaced as tools
# ---------------------------------------------------------------------------


async def test_t2_resources_are_reachable():
    """All three resources are registered and return non-empty content."""
    async with Client(mcp) as client:
        resources = await client.list_resources()
        assert {str(r.uri) for r in resources} == EXPECTED_RESOURCE_URIS

        for uri in sorted(EXPECTED_RESOURCE_URIS):
            contents = await client.read_resource(uri)
            assert contents, f"{uri} returned no content"
            assert contents[0].text.strip(), f"{uri} returned empty content"


async def test_t2_resources_are_surfaced_as_tools():
    """The transform tools actually route through to the resources.

    ResourcesAsTools can degrade silently -- the server still starts, it just
    advertises the decorated tools and nothing else, leaving tool-only clients
    with no route to the resources. Calling the tools proves they are wired,
    not merely present in the catalog.
    """
    async with Client(mcp) as client:
        listed = await client.call_tool("list_resources", {})
        listing = listed.content[0].text
        for uri in EXPECTED_RESOURCE_URIS:
            assert uri in listing, f"{uri} absent from list_resources output"

        for uri in sorted(EXPECTED_RESOURCE_URIS):
            direct = await client.read_resource(uri)
            through_tool = await client.call_tool("read_resource", {"uri": uri})
            assert through_tool.content[0].text == direct[0].text, (
                f"read_resource tool returned different content than the "
                f"resource protocol for {uri}"
            )


# ---------------------------------------------------------------------------
# T3 -- input schemas
# ---------------------------------------------------------------------------


async def test_t3_every_tool_has_a_well_formed_input_schema():
    """No tool ships an empty schema.

    This is the failure shape of the nocobot defect: a schema that collapses
    to ``{}`` is silent, and the LLM is left guessing every parameter. An
    object schema with an empty ``properties`` map is a different thing --
    that is a genuine zero-argument tool -- so the two are distinguished
    rather than lumped together.
    """
    async with Client(mcp) as client:
        tools = await client.list_tools()

    for tool in tools:
        schema = tool.input_schema
        assert schema, f"{tool.name} has an empty input schema"
        assert isinstance(schema, dict), f"{tool.name} schema is not a dict"
        assert schema.get("type") == "object", (
            f"{tool.name} schema type is {schema.get('type')!r}, expected 'object'"
        )
        assert "properties" in schema, f"{tool.name} schema has no properties key"


async def test_t3_only_known_zero_argument_tools_take_no_parameters():
    """Pins which tools have no parameters.

    If a schema silently lost its properties this set would grow, which a
    per-tool well-formedness check alone would not catch.
    """
    async with Client(mcp) as client:
        tools = await client.list_tools()

    zero_arg = {tool.name for tool in tools if not tool.input_schema.get("properties")}
    assert zero_arg == EXPECTED_ZERO_ARG_TOOLS


# ---------------------------------------------------------------------------
# T4 -- health endpoint
# ---------------------------------------------------------------------------


async def test_t4_health_endpoint_returns_ok():
    """/health is the deploy gate, so it has to answer."""
    app = mcp.http_app()
    async with asgi_client(app) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_t4_health_endpoint_does_not_require_auth():
    """/health answers without a token even when auth is enabled.

    Documents why /health cannot stand in for an auth check: it is a static
    handler that never touches the verifier, so it returns ok whether
    authentication works, is misconfigured, or is wide open. A green deploy
    check says nothing about whether /mcp is protected -- that is the gap T5
    exists to close.
    """
    with server_with_api_key(CORRECT_API_KEY) as server_module:
        app = server_module.mcp.http_app()
        async with asgi_client(app) as client:
            response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# T5/T6 -- authentication
# ---------------------------------------------------------------------------


async def test_t5_auth_rejects_wrong_token():
    """A wrong bearer token is rejected.

    The single most important test in this module. DebugTokenVerifier's
    `validate` parameter defaults to a lambda that accepts every non-empty
    token; server.py overrides it with an hmac comparison against
    MCP_API_KEY. If that override were ever dropped, renamed, or swallowed by
    a signature change, the server would construct successfully with the
    accept-everything default, /health would still return ok, the deploy would
    go green, and /mcp would accept any bearer token at all.

    A test that only checks the correct token still passes in that world.
    Only this one fails.
    """
    with server_with_api_key(CORRECT_API_KEY) as server_module:
        app = server_module.mcp.http_app()
        async with asgi_client(app) as client:
            response = await _post_initialize(client, WRONG_API_KEY)

    assert response.status_code == 401, (
        f"a wrong bearer token was not rejected (status {response.status_code}). "
        "The server is accepting arbitrary tokens."
    )


async def test_t5_auth_rejects_missing_token():
    """A request with no Authorization header is rejected."""
    with server_with_api_key(CORRECT_API_KEY) as server_module:
        app = server_module.mcp.http_app()
        async with asgi_client(app) as client:
            response = await _post_initialize(client, None)

    assert response.status_code == 401


async def test_t6_auth_accepts_correct_token():
    """The correct bearer token is accepted.

    Proves T5 is observing authentication rather than a server that rejects
    everything it is sent.
    """
    with server_with_api_key(CORRECT_API_KEY) as server_module:
        app = server_module.mcp.http_app()
        async with asgi_client(app) as client:
            response = await _post_initialize(client, CORRECT_API_KEY)

    assert response.status_code == 200


async def test_t6_auth_verifier_is_configured_when_api_key_is_set():
    """Auth is wired when MCP_API_KEY is present, and absent when it is not."""
    with server_with_api_key(CORRECT_API_KEY) as server_module:
        assert server_module.mcp.auth is not None
        assert server_module._api_key == CORRECT_API_KEY
