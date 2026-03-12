"""Tests for LLMProvider.chat_with_retry()."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from nocobot.providers.base import LLMProvider, LLMResponse


class StubProvider(LLMProvider):
    """Concrete stub for testing."""

    async def chat(self, messages, tools=None, model=None, max_tokens=4096, temperature=0.7):
        raise NotImplementedError

    def get_default_model(self) -> str:
        return "stub"


@pytest.mark.asyncio
@patch("nocobot.providers.base.asyncio.sleep", new_callable=AsyncMock)
async def test_transient_error_retries_then_succeeds(mock_sleep):
    provider = StubProvider()
    mock_chat = AsyncMock(side_effect=[
        LLMResponse(content="429 rate limit exceeded", finish_reason="error"),
        LLMResponse(content="Hello!", finish_reason="stop"),
    ])
    provider.chat = mock_chat

    result = await provider.chat_with_retry(messages=[{"role": "user", "content": "hi"}])

    assert result.finish_reason == "stop"
    assert result.content == "Hello!"
    assert mock_chat.call_count == 2
    mock_sleep.assert_awaited_once_with(1)


@pytest.mark.asyncio
@patch("nocobot.providers.base.asyncio.sleep", new_callable=AsyncMock)
async def test_non_transient_error_exits_immediately(mock_sleep):
    provider = StubProvider()
    mock_chat = AsyncMock(return_value=LLMResponse(
        content="Invalid API key", finish_reason="error"
    ))
    provider.chat = mock_chat

    result = await provider.chat_with_retry(messages=[{"role": "user", "content": "hi"}])

    assert result.finish_reason == "error"
    assert result.content == "Invalid API key"
    assert mock_chat.call_count == 1
    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
@patch("nocobot.providers.base.asyncio.sleep", new_callable=AsyncMock)
async def test_all_retries_exhausted(mock_sleep):
    provider = StubProvider()
    mock_chat = AsyncMock(return_value=LLMResponse(
        content="503 server error", finish_reason="error"
    ))
    provider.chat = mock_chat

    result = await provider.chat_with_retry(messages=[{"role": "user", "content": "hi"}])

    assert result.finish_reason == "error"
    assert mock_chat.call_count == 4  # 3 retries + 1 final
    assert mock_sleep.await_count == 3


@pytest.mark.asyncio
async def test_cancelled_error_is_reraised():
    provider = StubProvider()
    provider.chat = AsyncMock(side_effect=asyncio.CancelledError())

    with pytest.raises(asyncio.CancelledError):
        await provider.chat_with_retry(messages=[{"role": "user", "content": "hi"}])
