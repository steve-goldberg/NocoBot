"""NocoDB MCP Server resources for guiding tool usage.

Provides three resources:
- nocodb://workflow-guide: Critical rules for schema discovery
- nocodb://reference: Full reference documentation for all tools
- nocodb://formula-reference: Complete formula function and operator reference

Content is stored in separate markdown files under content/.
"""

from pathlib import Path

from .server import mcp

_CONTENT_DIR = Path(__file__).parent / "content"

WORKFLOW_CONTENT = (_CONTENT_DIR / "workflow-guide.md").read_text()
REFERENCE_CONTENT = (_CONTENT_DIR / "reference.md").read_text()
FORMULA_CONTENT = (_CONTENT_DIR / "formula-reference.md").read_text()


# =============================================================================
# Register resources with the MCP server
# =============================================================================


@mcp.resource(
    uri="nocodb://workflow-guide",
    name="NocoDB Workflow Guide",
    description="Critical rules for schema discovery - READ FIRST before using sort/where",
    mime_type="text/markdown",
)
def nocodb_workflow() -> str:
    """Critical workflow rules to prevent 400 errors when querying NocoDB."""
    return WORKFLOW_CONTENT


@mcp.resource(
    uri="nocodb://reference",
    name="NocoDB Reference",
    description="Complete reference documentation for all NocoDB MCP tools",
    mime_type="text/markdown",
)
def nocodb_reference() -> str:
    """Full reference documentation for NocoDB MCP server tools."""
    return REFERENCE_CONTENT


@mcp.resource(
    uri="nocodb://formula-reference",
    name="NocoDB Formula Reference",
    description="Complete formula function and operator reference for NocoDB",
    mime_type="text/markdown",
)
def nocodb_formula_reference() -> str:
    """Formula syntax reference for all NocoDB formula functions."""
    return FORMULA_CONTENT
