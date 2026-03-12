"""NocoDB MCP Server resources.

Provides three resources:
- nocodb://schema-discovery-rules: Critical rules for schema discovery
- nocodb://tools-reference: Full reference documentation for all tools
- nocodb://formula-reference: Complete formula function and operator reference

Content is stored in markdown files alongside this module.
"""

from pathlib import Path

from ..server import mcp

_DIR = Path(__file__).parent

SCHEMA_DISCOVERY_CONTENT = (_DIR / "schema-discovery-rules.md").read_text()
TOOLS_REFERENCE_CONTENT = (_DIR / "tools-reference.md").read_text()
FORMULA_CONTENT = (_DIR / "formula-reference.md").read_text()


# =============================================================================
# Register resources with the MCP server
# =============================================================================


@mcp.resource(
    uri="nocodb://schema-discovery-rules",
    name="NocoDB Schema Discovery Rules",
    description="Critical rules for schema discovery - READ FIRST before using sort/where",
    mime_type="text/markdown",
)
def nocodb_schema_discovery_rules() -> str:
    """Critical workflow rules to prevent 400 errors when querying NocoDB."""
    return SCHEMA_DISCOVERY_CONTENT


@mcp.resource(
    uri="nocodb://tools-reference",
    name="NocoDB Tools Reference",
    description="Complete reference documentation for all NocoDB MCP tools",
    mime_type="text/markdown",
)
def nocodb_tools_reference() -> str:
    """Full reference documentation for NocoDB MCP server tools."""
    return TOOLS_REFERENCE_CONTENT


@mcp.resource(
    uri="nocodb://formula-reference",
    name="NocoDB Formula Reference",
    description="Complete formula function and operator reference for NocoDB",
    mime_type="text/markdown",
)
def nocodb_formula_reference() -> str:
    """Formula syntax reference for all NocoDB formula functions."""
    return FORMULA_CONTENT
