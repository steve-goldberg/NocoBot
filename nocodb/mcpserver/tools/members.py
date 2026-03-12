"""Members tools for NocoDB MCP server.

Provides operations for base member management:
- members_list: List all members of the base
- member_add: Add a new member to the base
- member_update: Update a member's role
- member_remove: Remove a member from the base (requires confirm=True)
"""

from typing import Optional

from ..server import mcp
from ..dependencies import get_client, get_base_id
from ..errors import wrap_api_error
from ..models import MembersListResult, MemberResult, MemberDeleteResult


@mcp.tool
@wrap_api_error
def members_list() -> MembersListResult:
    """List all members of the current base.

    Returns:
        MembersListResult with list of members including id, email, and roles.
    """
    client = get_client()
    base_id = get_base_id()

    result = client.base_members_list(base_id)
    members = result.get("members", result.get("list", []))

    return MembersListResult(members=members)


@mcp.tool
@wrap_api_error
def member_add(
    email: str,
    role: str = "editor",
) -> MemberResult:
    """Add a new member to the current base.

    Args:
        email: The user's email address
        role: The role to assign. Options:
            - owner: Full control
            - creator: Can create tables
            - editor: Can edit records
            - commenter: Can comment only
            - viewer: Read-only access

    Returns:
        MemberResult with the added member details.
    """
    client = get_client()
    base_id = get_base_id()

    body = {"email": email, "roles": role}
    result = client.base_member_add(base_id, body)

    return MemberResult(
        id=result.get("id", ""),
        email=result.get("email", email),
        roles=result.get("roles", role),
    )


@mcp.tool
@wrap_api_error
def member_update(
    member_id: str,
    role: str,
) -> MemberResult:
    """Update a member's role.

    Args:
        member_id: The member ID
        role: The new role. Options:
            - owner: Full control
            - creator: Can create tables
            - editor: Can edit records
            - commenter: Can comment only
            - viewer: Read-only access

    Returns:
        MemberResult with updated member details.
    """
    client = get_client()
    base_id = get_base_id()

    body = {"roles": role}
    result = client.base_member_update(base_id, member_id, body)

    return MemberResult(
        id=result.get("id", member_id),
        email=result.get("email", ""),
        roles=result.get("roles", role),
    )


@mcp.tool(annotations={
    "title": "Remove Member",
    "destructiveHint": True,
    "idempotentHint": True,
})
@wrap_api_error
def member_remove(
    member_id: str,
    confirm: bool = False,
) -> MemberDeleteResult:
    """Remove a member from the base.

    The user will lose access to this base but their NocoDB account
    is not affected.

    Args:
        member_id: The member ID to remove
        confirm: Must be True to proceed with removal

    Returns:
        MemberDeleteResult with success status.
    """
    if not confirm:
        from fastmcp.exceptions import ToolError
        raise ToolError(
            "Set confirm=True to remove this member. "
            "The user will lose access to this base."
        )

    client = get_client()
    base_id = get_base_id()

    client.base_member_remove(base_id, member_id)

    return MemberDeleteResult(
        success=True,
        message=f"Member {member_id} removed from base",
    )
