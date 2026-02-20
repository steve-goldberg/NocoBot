"""Base channel interface for chat platforms."""

import re
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from nocobot.bus.events import InboundMessage, OutboundMessage
from nocobot.bus.queue import MessageBus
from nocobot.ratelimit import TokenBucket

# Control characters (C0 and C1) except tab, newline, carriage return
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


class BaseChannel(ABC):
    """
    Abstract base class for chat channel implementations.
    
    Each channel (Telegram, Discord, etc.) should implement this interface
    to integrate with the nocobot message bus.
    """
    
    name: str = "base"
    
    def __init__(self, config: Any, bus: MessageBus):
        """
        Initialize the channel.
        
        Args:
            config: Channel-specific configuration.
            bus: The message bus for communication.
        """
        self.config = config
        self.bus = bus
        self._running = False

        # Input validation
        self._max_message_length: int = getattr(config, "max_message_length", 4096)

        # Per-user rate limiter
        capacity = getattr(config, "rate_limit_messages", 10)
        window = getattr(config, "rate_limit_window", 60.0)
        self._rate_limiter: TokenBucket | None = (
            TokenBucket(capacity, window) if capacity > 0 else None
        )
    
    @abstractmethod
    async def start(self) -> None:
        """
        Start the channel and begin listening for messages.
        
        This should be a long-running async task that:
        1. Connects to the chat platform
        2. Listens for incoming messages
        3. Forwards messages to the bus via _handle_message()
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel and clean up resources."""
        pass
    
    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None:
        """
        Send a message through this channel.
        
        Args:
            msg: The message to send.
        """
        pass
    
    def is_allowed(self, sender_id: str) -> bool:
        """
        Check if a sender is allowed to use this bot.
        
        Args:
            sender_id: The sender's identifier.
        
        Returns:
            True if allowed, False otherwise.
        """
        allow_list = getattr(self.config, "allow_from", [])
        
        # If no allow list, allow everyone
        if not allow_list:
            return True
        
        sender_str = str(sender_id)
        if sender_str in allow_list:
            return True
        if "|" in sender_str:
            for part in sender_str.split("|"):
                if part and part in allow_list:
                    return True
        return False
    
    @staticmethod
    def _sanitize_content(content: str) -> str:
        """Strip null bytes and control characters, preserving tab/newline/CR."""
        return _CONTROL_CHAR_RE.sub("", content)

    async def _handle_message(
        self,
        sender_id: str,
        chat_id: str,
        content: str,
        media: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Handle an incoming message from the chat platform.

        Checks permissions, validates input, enforces rate limits,
        and forwards to the bus.
        """
        # 1. Permission check
        if not self.is_allowed(sender_id):
            logger.warning(
                f"Access denied for sender {sender_id} on channel {self.name}. "
                f"Add them to allowFrom list in config to grant access."
            )
            return

        # 2. Sanitize content
        content = self._sanitize_content(content)

        # 3. Length check
        if len(content) > self._max_message_length:
            logger.warning(
                f"Message too long from {sender_id}: {len(content)} chars "
                f"(max {self._max_message_length})"
            )
            await self.bus.publish_outbound(OutboundMessage(
                channel=self.name,
                chat_id=str(chat_id),
                content=(
                    f"Message too long ({len(content)} characters). "
                    f"Please keep messages under {self._max_message_length} characters."
                ),
            ))
            return

        # 4. Per-user rate limiting
        if self._rate_limiter is not None:
            rate_key = str(sender_id).split("|")[0]
            if not self._rate_limiter.consume(rate_key):
                logger.warning(f"Rate limited sender {sender_id} on channel {self.name}")
                await self.bus.publish_outbound(OutboundMessage(
                    channel=self.name,
                    chat_id=str(chat_id),
                    content="You're sending messages too quickly. Please wait a moment.",
                ))
                return

        # 5. Publish to bus
        msg = InboundMessage(
            channel=self.name,
            sender_id=str(sender_id),
            chat_id=str(chat_id),
            content=content,
            media=media or [],
            metadata=metadata or {}
        )

        await self.bus.publish_inbound(msg)
    
    @property
    def is_running(self) -> bool:
        """Check if the channel is running."""
        return self._running
