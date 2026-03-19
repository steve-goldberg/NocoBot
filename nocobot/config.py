"""Configuration for nocobot - NocoDB Telegram Agent."""

from typing import Literal

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
    nocodb_mcp_url: str = "http://localhost:8000/mcp"
    nocodb_mcp_api_key: str = ""
    nocodb_mcp_tool_timeout: int = 30

    # Agent limits
    agent_max_iterations: int = 10
    agent_message_timeout: float = 300.0
    agent_max_history: int = 40
    agent_max_tokens: int = 200_000

    # Agent tuning
    agent_tool_result_max: int = 500
    agent_tool_result_inference_max: int = 4000
    agent_max_concurrency: int = 3
    agent_session_max_idle: float = 3600.0

    # LLM defaults
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7

    # Vision
    vision_max_images: int = 5
    vision_max_long_edge: int = 1024
    vision_detail: Literal["low", "high", "auto"] = "low"

    # Input validation
    max_message_length: int = 4096

    # Media file limits
    media_max_file_size: int = 20_971_520      # 20 MB per file
    media_max_total_size: int = 524_288_000     # 500 MB total media dir cap

    # Telegram transport
    telegram_max_chunk_length: int = 4000
    telegram_connection_pool_size: int = 16

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
