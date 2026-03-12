"""Dependency injection and configuration for NocoDB MCP server.

Environment variables:
    NOCODB_URL: NocoDB server URL (required)
    NOCODB_TOKEN: API token or JWT (required)
    NOCODB_BASE_ID: Default base ID (required)
    NOCODB_VERIFY_SSL: Set to "false" to skip SSL verification (optional, for self-signed certs)
"""

import os
from dataclasses import dataclass
from typing import Optional

from nocodb import APIToken, JWTAuthToken
from nocodb.infra.requests_client import NocoDBRequestsClient


@dataclass
class MCPConfig:
    """MCP server configuration loaded from environment."""
    url: str
    token: str
    base_id: str
    verify_ssl: bool = True

    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Load configuration from environment variables.

        Raises:
            ValueError: If required environment variables are missing.
        """
        url = os.environ.get("NOCODB_URL", "")
        token = os.environ.get("NOCODB_TOKEN", "")
        base_id = os.environ.get("NOCODB_BASE_ID", "")
        verify_ssl = os.environ.get("NOCODB_VERIFY_SSL", "true").lower() not in ("false", "0", "no")

        missing = []
        if not url:
            missing.append("NOCODB_URL")
        if not token:
            missing.append("NOCODB_TOKEN")
        if not base_id:
            missing.append("NOCODB_BASE_ID")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Set NOCODB_URL, NOCODB_TOKEN, and NOCODB_BASE_ID."
            )

        return cls(url=url, token=token, base_id=base_id, verify_ssl=verify_ssl)

    def is_jwt(self) -> bool:
        """Check if token is a JWT (starts with eyJ)."""
        return self.token.startswith("eyJ")


def create_client(config: MCPConfig) -> NocoDBRequestsClient:
    """Create a NocoDB client from MCP configuration.

    Args:
        config: MCP configuration with URL and token.

    Returns:
        Configured NocoDBRequestsClient instance.
    """
    if config.is_jwt():
        auth = JWTAuthToken(config.token)
    else:
        auth = APIToken(config.token)

    # TODO: Remove verify_ssl=False once proper SSL certs are configured
    return NocoDBRequestsClient(auth, config.url, verify_ssl=config.verify_ssl)


# Module-level state for lifespan-managed resources
_config: Optional[MCPConfig] = None
_client: Optional[NocoDBRequestsClient] = None


def get_config() -> MCPConfig:
    """Get the MCP configuration.

    Returns:
        Current MCPConfig instance.

    Raises:
        RuntimeError: If config not initialized (server not started).
    """
    if _config is None:
        raise RuntimeError(
            "MCP server not initialized. Config is set during server lifespan."
        )
    return _config


def get_client() -> NocoDBRequestsClient:
    """Get the NocoDB client.

    Returns:
        Current NocoDBRequestsClient instance.

    Raises:
        RuntimeError: If client not initialized (server not started).
    """
    if _client is None:
        raise RuntimeError(
            "MCP server not initialized. Client is created during server lifespan."
        )
    return _client


def get_base_id() -> str:
    """Get the configured base ID.

    Returns:
        Base ID from configuration.

    Raises:
        RuntimeError: If config not initialized.
    """
    return get_config().base_id


def init_dependencies() -> tuple[MCPConfig, NocoDBRequestsClient]:
    """Initialize dependencies during server startup.

    Called by server lifespan. Sets module-level state.

    Returns:
        Tuple of (config, client).
    """
    global _config, _client
    _config = MCPConfig.from_env()
    _client = create_client(_config)
    return _config, _client


def cleanup_dependencies() -> None:
    """Cleanup dependencies during server shutdown.

    Called by server lifespan. Clears module-level state.
    """
    global _config, _client
    _config = None
    _client = None
