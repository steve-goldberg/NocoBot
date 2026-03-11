"""Main entry point for nocobot - NocoDB Telegram Agent."""

from __future__ import annotations

import asyncio
import signal
from loguru import logger

from nocobot.agent import AgentLoop
from nocobot.bus.queue import MessageBus
from nocobot.channels.telegram import TelegramChannel, TelegramConfig
from nocobot.config import load_config
from nocobot.mcp_client import MCPClient


async def main() -> None:
    """Run nocobot."""
    # Load configuration
    config = load_config()
    logger.info("Configuration loaded")

    # Initialize components
    bus = MessageBus()

    # Initialize MCP client and connect
    mcp = MCPClient(config.nocodb_mcp_url, tool_timeout=config.nocodb_mcp_tool_timeout)
    await mcp.connect()

    # Initialize Telegram channel
    telegram_config = TelegramConfig(
        token=config.telegram_token,
        allow_from=config.telegram_allow_from or None,
        max_message_length=config.max_message_length,
        rate_limit_messages=config.rate_limit_messages,
        rate_limit_window=config.rate_limit_window,
    )
    telegram = TelegramChannel(telegram_config, bus)

    # Initialize agent
    agent = AgentLoop(
        bus=bus,
        mcp=mcp,
        api_key=config.openrouter_api_key,
        model=config.openrouter_model,
        max_iterations=config.agent_max_iterations,
        max_history=config.agent_max_history,
        message_timeout=config.agent_message_timeout,
        max_tokens_budget=config.agent_max_tokens,
    )

    # Set up graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler() -> None:
        logger.info("Shutdown signal received")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Start components
    async def run_telegram() -> None:
        await telegram.start()

    async def run_agent() -> None:
        await agent.start()

    async def dispatch_outbound() -> None:
        """Route outbound messages to Telegram."""
        while not shutdown_event.is_set():
            try:
                msg = await asyncio.wait_for(bus.consume_outbound(), timeout=1.0)
                if msg.channel == "telegram":
                    await telegram.send(msg)
            except asyncio.TimeoutError:
                continue

    # Run all tasks
    tasks = [
        asyncio.create_task(run_telegram()),
        asyncio.create_task(run_agent()),
        asyncio.create_task(dispatch_outbound()),
    ]

    logger.info("Nocobot started - press Ctrl+C to stop")

    # Wait for shutdown
    await shutdown_event.wait()

    # Graceful shutdown
    logger.info("Shutting down...")
    await telegram.stop()
    await agent.stop()
    bus.stop()

    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    logger.info("Nocobot stopped")


def run() -> None:
    """Entry point for the application."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
