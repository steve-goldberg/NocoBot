"""Tests for agent loop — tool result persistence in conversation history."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from nocobot.agent import AgentLoop
from nocobot.bus.events import InboundMessage
from nocobot.bus.queue import MessageBus
from nocobot.providers.base import LLMResponse, ToolCallRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_msg(content: str = "hello", session_key: str = "test:1") -> InboundMessage:
    channel, chat_id = session_key.split(":", 1)
    return InboundMessage(
        channel=channel, sender_id="user", chat_id=chat_id, content=content,
    )


def _make_agent(
    llm_responses: list[LLMResponse] | None = None,
    mcp_tool_results: dict[str, str] | None = None,
) -> AgentLoop:
    """Create an AgentLoop with mocked LLM and MCP."""
    bus = MessageBus()
    mcp = AsyncMock()
    mcp.get_system_prompt.return_value = "You are a test assistant."
    mcp.get_tools_for_llm.return_value = [
        {"type": "function", "function": {"name": "test_tool", "description": "test", "parameters": {}}},
    ]

    tool_results = mcp_tool_results or {}
    async def _call_tool(name: str, arguments: Any) -> str:
        return tool_results.get(name, f"result for {name}")
    mcp.call_tool = _call_tool

    agent = AgentLoop(
        bus=bus,
        mcp=mcp,
        api_key="test-key",
        model="test-model",
        max_iterations=10,
        max_history=40,
        message_timeout=30.0,
        max_tokens_budget=200_000,
    )
    agent._system_prompt = "You are a test assistant."

    # Mock LLM responses
    responses = list(llm_responses or [])
    agent._llm = AsyncMock()
    agent._llm.chat_with_retry = AsyncMock(side_effect=responses)

    return agent


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestToolResultPersistence:
    """Tool calls and results must persist in conversation history."""

    @pytest.mark.asyncio
    async def test_simple_response_saved_to_history(self):
        """A simple text response saves user + assistant to history."""
        agent = _make_agent(llm_responses=[
            LLMResponse(content="Hello!", usage={"total_tokens": 100}),
        ])
        msg = _make_msg("hi")
        await agent._process_message(msg)

        history = agent._history["test:1"]
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "hi"}
        assert history[1] == {"role": "assistant", "content": "Hello!"}

    @pytest.mark.asyncio
    async def test_tool_calls_and_results_saved_to_history(self):
        """Tool call assistant msgs and tool results persist across turns."""
        agent = _make_agent(
            llm_responses=[
                # Iteration 1: LLM requests a tool call
                LLMResponse(
                    content="Let me check.",
                    tool_calls=[ToolCallRequest(id="tc_1", name="test_tool", arguments={})],
                    usage={"total_tokens": 100},
                ),
                # Iteration 2: LLM gives final response
                LLMResponse(content="Here are the results.", usage={"total_tokens": 100}),
            ],
            mcp_tool_results={"test_tool": "tool output data"},
        )

        msg = _make_msg("list tables")
        await agent._process_message(msg)

        history = agent._history["test:1"]
        assert len(history) == 4

        # 1. User message
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "list tables"

        # 2. Assistant with tool_calls
        assert history[1]["role"] == "assistant"
        assert "tool_calls" in history[1]
        assert history[1]["tool_calls"][0]["function"]["name"] == "test_tool"

        # 3. Tool result
        assert history[2]["role"] == "tool"
        assert history[2]["tool_call_id"] == "tc_1"
        assert history[2]["content"] == "tool output data"

        # 4. Final assistant response
        assert history[3]["role"] == "assistant"
        assert history[3]["content"] == "Here are the results."

    @pytest.mark.asyncio
    async def test_history_available_on_second_turn(self):
        """Second message's LLM call includes tool results from first turn."""
        agent = _make_agent(
            llm_responses=[
                # Turn 1: tool call + final
                LLMResponse(
                    content="",
                    tool_calls=[ToolCallRequest(id="tc_1", name="test_tool", arguments={})],
                    usage={"total_tokens": 100},
                ),
                LLMResponse(content="Found 3 tables.", usage={"total_tokens": 100}),
                # Turn 2: simple response
                LLMResponse(content="Yes, I found 3 tables earlier.", usage={"total_tokens": 100}),
            ],
            mcp_tool_results={"test_tool": "tables: A, B, C"},
        )

        await agent._process_message(_make_msg("list tables"))
        await agent._process_message(_make_msg("what tables did you find?"))

        # Check the messages sent to LLM on the second call
        second_call_messages = agent._llm.chat_with_retry.call_args_list[2].kwargs["messages"]
        roles = [m["role"] for m in second_call_messages]

        # Should include: system, user(turn1), assistant+tool_calls, tool, assistant, user(turn2)
        assert "tool" in roles, "Tool results should be in second turn's context"
        assert roles.count("user") == 2, "Both user messages should be present"


class TestTwoTierTruncation:
    """Tool results truncated at execute-time and save-time with different limits."""

    @pytest.mark.asyncio
    async def test_inference_truncation(self):
        """Results > 4000 chars are truncated at execute-time."""
        big_result = "x" * 5000
        agent = _make_agent(
            llm_responses=[
                LLMResponse(
                    content="",
                    tool_calls=[ToolCallRequest(id="tc_1", name="test_tool", arguments={})],
                    usage={"total_tokens": 100},
                ),
                LLMResponse(content="Done.", usage={"total_tokens": 100}),
            ],
            mcp_tool_results={"test_tool": big_result},
        )

        await agent._process_message(_make_msg("test"))

        # Check what the LLM received on second iteration
        second_call_messages = agent._llm.chat_with_retry.call_args_list[1].kwargs["messages"]
        tool_msg = [m for m in second_call_messages if m["role"] == "tool"][0]
        assert len(tool_msg["content"]) <= 4000 + 20  # 4000 + "\n... (truncated)"
        assert tool_msg["content"].endswith("... (truncated)")

    @pytest.mark.asyncio
    async def test_history_truncation_tighter(self):
        """Results > 500 chars are further truncated when saved to history."""
        medium_result = "y" * 2000  # Under inference limit, over history limit
        agent = _make_agent(
            llm_responses=[
                LLMResponse(
                    content="",
                    tool_calls=[ToolCallRequest(id="tc_1", name="test_tool", arguments={})],
                    usage={"total_tokens": 100},
                ),
                LLMResponse(content="Done.", usage={"total_tokens": 100}),
            ],
            mcp_tool_results={"test_tool": medium_result},
        )

        await agent._process_message(_make_msg("test"))

        history = agent._history["test:1"]
        tool_entry = [m for m in history if m["role"] == "tool"][0]
        assert len(tool_entry["content"]) <= 500 + 20  # 500 + "\n... (truncated)"
        assert tool_entry["content"].endswith("... (truncated)")


class TestHistoryTrimming:
    """History trimming aligns to user turn boundaries."""

    def test_trim_at_user_boundary(self):
        agent = _make_agent()
        history: list[dict[str, Any]] = []

        # Simulate 3 turns with tool calls (12 messages each: user + assistant+tc + tool + assistant)
        for i in range(15):
            history.append({"role": "user", "content": f"msg {i}"})
            history.append({"role": "assistant", "content": "", "tool_calls": [{"id": f"tc_{i}"}]})
            history.append({"role": "tool", "tool_call_id": f"tc_{i}", "content": "result"})
            history.append({"role": "assistant", "content": f"response {i}"})

        assert len(history) == 60
        agent.max_history = 20
        agent._trim_history(history)

        # Should start with a user message
        assert history[0]["role"] == "user"
        assert len(history) <= 20

    def test_no_orphaned_tool_results(self):
        agent = _make_agent()
        history: list[dict[str, Any]] = [
            {"role": "assistant", "content": "", "tool_calls": [{"id": "tc_old"}]},
            {"role": "tool", "tool_call_id": "tc_old", "content": "old result"},
            {"role": "assistant", "content": "old response"},
            {"role": "user", "content": "newer msg"},
            {"role": "assistant", "content": "newer response"},
        ]

        agent.max_history = 4
        agent._trim_history(history)

        # Should skip the orphaned tool result and start at the user message
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "newer msg"


class TestLLMErrorNoSave:
    """LLM errors should not pollute history."""

    @pytest.mark.asyncio
    async def test_error_response_not_saved(self):
        agent = _make_agent(llm_responses=[
            LLMResponse(content="LLM request failed (500)", finish_reason="error", usage={}),
        ])

        await agent._process_message(_make_msg("hello"))

        history = agent._history.get("test:1", [])
        assert len(history) == 0, "LLM errors should not save anything to history"


class TestSaveTurnUnit:
    """Unit tests for _save_turn method."""

    def test_skips_empty_assistant(self):
        agent = _make_agent()
        history: list[dict[str, Any]] = []
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": ""},  # empty, no tool_calls
            {"role": "assistant", "content": "hello"},
        ]
        agent._save_turn(history, messages, skip=1)

        roles = [m["role"] for m in history]
        assert roles == ["user", "assistant"]
        assert history[1]["content"] == "hello"

    def test_keeps_assistant_with_tool_calls(self):
        agent = _make_agent()
        history: list[dict[str, Any]] = []
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "", "tool_calls": [{"id": "tc_1"}]},
            {"role": "tool", "tool_call_id": "tc_1", "content": "result"},
            {"role": "assistant", "content": "done"},
        ]
        agent._save_turn(history, messages, skip=1)

        roles = [m["role"] for m in history]
        assert roles == ["user", "assistant", "tool", "assistant"]
        assert "tool_calls" in history[1]
