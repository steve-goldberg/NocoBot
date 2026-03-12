"""Error handling utilities for NocoDB MCP server."""

from typing import Callable, TypeVar, ParamSpec
from functools import wraps

from fastmcp.exceptions import ToolError

from nocodb.exceptions import NocoDBAPIError

P = ParamSpec("P")
T = TypeVar("T")


def wrap_api_error(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator to convert NocoDBAPIError to ToolError.

    This ensures API errors are properly surfaced to the MCP client
    with meaningful error messages.
    """
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except NocoDBAPIError as e:
            # Extract useful error details
            details = []
            if e.status_code:
                details.append(f"Status: {e.status_code}")
            if e.response_json:
                msg = e.response_json.get("msg") or e.response_json.get("message")
                if msg:
                    details.append(f"Message: {msg}")

            error_msg = str(e)
            if details:
                error_msg = f"{error_msg} ({', '.join(details)})"

            raise ToolError(error_msg) from e

    return wrapper


def require_confirm(operation: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to require confirm=True for destructive operations.

    Args:
        operation: Description of the destructive operation (e.g., "delete records")

    Usage:
        @require_confirm("delete records")
        def records_delete(table_id: str, record_ids: list[str], confirm: bool = False):
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Check for confirm in kwargs
            confirm = kwargs.get("confirm", False)
            if not confirm:
                raise ToolError(
                    f"Set confirm=True to {operation}. "
                    f"This is a destructive operation that cannot be undone."
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
