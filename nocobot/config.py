"""Configuration for nocobot - NocoDB Telegram Agent."""

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Nocobot configuration loaded from environment variables."""

    # Telegram
    telegram_token: str
    telegram_allow_from: list[str] = []

    # OpenRouter LLM
    openrouter_api_key: str
    openrouter_model: str = "anthropic/claude-sonnet-4"

    # NocoDB MCP Server
    nocodb_mcp_url: str = "http://ncdbmcp.lab/mcp"

    # Agent limits
    agent_max_iterations: int = 10
    agent_message_timeout: float = 300.0
    agent_max_history: int = 40
    agent_max_tokens: int = 200_000

    # Input validation
    max_message_length: int = 4096

    # Per-user rate limiting
    rate_limit_messages: int = 10
    rate_limit_window: float = 60.0

    model_config = {
        "env_prefix": "",
        "env_file": ".env",
        "extra": "ignore",
    }


def load_config() -> Config:
    """Load configuration from environment."""
    return Config()
