"""Chat channels module."""

from nocobot.channels.base import BaseChannel
from nocobot.channels.telegram import TelegramChannel

__all__ = ["BaseChannel", "TelegramChannel"]
