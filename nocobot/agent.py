"""Agent loop for nocobot - processes messages and calls MCP tools."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from loguru import logger

from nocobot.bus.events import InboundMessage, OutboundMessage
from nocobot.bus.queue import MessageBus
from nocobot.mcp_client import MCPClient
from nocobot.providers import LiteLLMProvider, ToolCallRequest


class AgentLoop:
    """Agent that processes messages using LLM and MCP tools."""

    _TOOL_RESULT_MAX = 500             # history storage (save-time)
    _TOOL_RESULT_INFERENCE_MAX = 4000  # current-turn LLM context (execute-time)

    def __init__(
        self,
        bus: MessageBus,
        mcp: MCPClient,
        api_key: str,
        model: str,
        max_iterations: int,
        max_history: int,
        message_timeout: float,
        max_tokens_budget: int,
    ):
        self.bus = bus
        self.mcp = mcp
        self.max_iterations = max_iterations
        self.max_history = max_history
        self.message_timeout = message_timeout
        self.max_tokens_budget = max_tokens_budget
        self._running = False
        self._semaphore = asyncio.Semaphore(3)
        self._session_locks: dict[str, asyncio.Lock] = {}
        self._tasks: set[asyncio.Task] = set()
        self._session_tasks: dict[str, asyncio.Task] = {}
        self._session_last_active: dict[str, float] = {}
        self._last_eviction: float = 0.0

        # In-memory conversation history per chat_id
        self._history: dict[str, list[dict[str, Any]]] = {}

        # LLM provider (OpenRouter)
        self._llm = LiteLLMProvider(
            api_key=api_key,
            default_model=model,
            provider_name="openrouter",
        )

        # System prompt (built from MCP resources)
        self._system_prompt = ""

    async def start(self) -> None:
        """Start the agent loop."""
        self._running = True
        self._system_prompt = self.mcp.get_system_prompt()
        logger.info("Agent loop started")

        while self._running:
            try:
                msg = await asyncio.wait_for(
                    self.bus.consume_inbound(),
                    timeout=1.0
                )
                if msg.content.strip() == "/stop":
                    await self._handle_stop(msg)
                    continue
                task = asyncio.create_task(self._handle_with_guard(msg))
                self._session_tasks[msg.session_key] = task
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
            except asyncio.TimeoutError:
                now = time.monotonic()
                if now - self._last_eviction > 60.0:
                    self._evict_stale_sessions()
                    self._last_eviction = now
                continue
            except Exception as e:
                logger.error(f"Agent error: {e}")

    async def stop(self) -> None:
        """Stop the agent loop."""
        self._running = False
        for task in list(self._tasks):
            task.cancel()
        self._session_tasks.clear()
        logger.info("Agent loop stopped")

    async def _handle_stop(self, msg: InboundMessage) -> None:
        """Cancel active processing for a session. Bypasses session lock."""
        task = self._session_tasks.pop(msg.session_key, None)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled active task for {msg.session_key}")
        self._history.pop(msg.session_key, None)
        self._session_locks.pop(msg.session_key, None)
        self._session_last_active.pop(msg.session_key, None)
        await self._send_response(msg, "Stopped. Conversation cleared.")

    def _evict_stale_sessions(self, max_idle: float = 3600.0) -> None:
        """Remove sessions idle longer than max_idle seconds."""
        now = time.monotonic()
        stale = [
            key for key, last in self._session_last_active.items()
            if now - last > max_idle
        ]
        for key in stale:
            self._history.pop(key, None)
            self._session_locks.pop(key, None)
            self._session_tasks.pop(key, None)
            self._session_last_active.pop(key, None)
        if stale:
            logger.info(f"Evicted {len(stale)} stale sessions")

    async def _handle_with_guard(self, msg: InboundMessage) -> None:
        """Process a message with per-session lock, semaphore, timeout, and error handling."""
        lock = self._session_locks.setdefault(msg.session_key, asyncio.Lock())
        async with lock:
            async with self._semaphore:
                try:
                    await asyncio.wait_for(
                        self._process_message(msg),
                        timeout=self.message_timeout,
                    )
                except asyncio.CancelledError:
                    logger.info(f"Task cancelled for {msg.session_key}")
                    raise
                except asyncio.TimeoutError:
                    logger.warning(
                        f"Message processing timed out after {self.message_timeout}s "
                        f"for {msg.session_key}"
                    )
                    await self._send_response(
                        msg,
                        "Sorry, that request took too long to process. "
                        "Try a simpler request or start fresh with /new."
                    )
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await self._send_response(
                        msg,
                        "Something went wrong processing your request. Please try again."
                    )

    async def _process_message(self, msg: InboundMessage) -> None:
        """Process an inbound message."""
        self._session_last_active[msg.session_key] = time.monotonic()
        logger.debug(f"Processing message from {msg.sender_id}: {msg.content[:50]}...")

        # Handle /new command - clear history
        if msg.content.strip() == "/new":
            self._history.pop(msg.session_key, None)
            self._session_last_active.pop(msg.session_key, None)
            await self._send_response(msg, "Conversation cleared. Starting fresh!")
            return

        # Handle /help command
        if msg.content.strip() == "/help":
            help_text = (
                "I'm nocobot, your NocoDB assistant.\n\n"
                "I can help you:\n"
                "- List tables and fields\n"
                "- Query and filter records\n"
                "- Create, update, and delete data\n"
                "- Manage views, filters, and sorts\n\n"
                "Commands:\n"
                "/new - Start a new conversation\n"
                "/stop - Stop the current operation\n"
                "/help - Show this help message\n\n"
                "Just tell me what you want to do with your NocoDB data!"
            )
            await self._send_response(msg, help_text)
            return

        # Get or create conversation history
        history = self._history.setdefault(msg.session_key, [])

        # Build messages for LLM (user message added to messages, not history yet)
        messages: list[dict[str, Any]] = (
            [{"role": "system", "content": self._system_prompt}]
            + list(history)
        )
        skip = len(messages)  # new messages (including user msg) start here
        messages.append({"role": "user", "content": msg.content})

        # Get MCP tools
        tools = self.mcp.get_tools_for_llm()

        # Agent loop - call LLM, execute tools, repeat
        total_tokens = 0
        start_time = time.monotonic()

        for iteration in range(self.max_iterations):
            response = await self._llm.chat_with_retry(
                messages=messages,
                tools=tools if tools else None,
                max_tokens=4096,
                temperature=0.7,
            )

            # Bail on LLM error — don't append to history (prevents context poisoning)
            if response.finish_reason == "error":
                logger.error(f"LLM error for {msg.session_key}: {response.content}")
                await self._send_response(
                    msg,
                    "Sorry, I'm having trouble reaching the AI service. "
                    "Please try again in a moment.",
                )
                return

            # Track token usage
            iter_tokens = response.usage.get("total_tokens", 0)
            total_tokens += iter_tokens
            elapsed = time.monotonic() - start_time

            logger.info(
                f"[{msg.session_key}] iteration={iteration + 1}/{self.max_iterations} "
                f"tools={len(response.tool_calls)} "
                f"tokens={iter_tokens} total={total_tokens} "
                f"elapsed={elapsed:.1f}s"
            )

            # If no tool calls, we're done
            if not response.has_tool_calls:
                if response.content:
                    messages.append({"role": "assistant", "content": response.content})
                    await self._send_response(msg, response.content)
                self._save_turn(history, messages, skip)
                return

            # Check token budget before executing more tool calls
            if total_tokens >= self.max_tokens_budget:
                logger.warning(
                    f"Token budget exceeded ({total_tokens}/{self.max_tokens_budget}) "
                    f"for {msg.session_key}"
                )
                # Ask LLM to summarize what it has so far
                summary = response.content or "I used a lot of resources on this request."
                messages.append({"role": "assistant", "content": summary})
                self._save_turn(history, messages, skip)
                await self._send_response(
                    msg,
                    f"{summary}\n\n_(Token budget reached - try /new for a fresh start)_"
                )
                return

            # Execute tool calls
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": response.content or ""}
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": tc.arguments},
                }
                for tc in response.tool_calls
            ]
            messages.append(assistant_msg)

            # Send progress message if LLM included text alongside tool calls
            if response.content:
                await self._send_response(msg, response.content, progress=True)

            # Execute each tool call
            for tc in response.tool_calls:
                result = await self._execute_tool(tc)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        # Max iterations reached
        elapsed = time.monotonic() - start_time
        logger.warning(
            f"Max iterations ({self.max_iterations}) reached for {msg.session_key} "
            f"total_tokens={total_tokens} elapsed={elapsed:.1f}s"
        )
        max_iter_msg = (
            f"I've reached the maximum of {self.max_iterations} iterations "
            f"({elapsed:.0f}s elapsed). Try breaking your request into smaller "
            f"steps or start fresh with /new."
        )
        messages.append({"role": "assistant", "content": max_iter_msg})
        self._save_turn(history, messages, skip)
        await self._send_response(msg, max_iter_msg)

    def _save_turn(
        self, history: list[dict[str, Any]], messages: list[dict], skip: int,
    ) -> None:
        """Persist new messages from the agent loop into session history."""
        for m in messages[skip:]:
            entry = dict(m)
            role, content = entry.get("role"), entry.get("content")
            if role == "assistant" and not content and not entry.get("tool_calls"):
                continue
            if (
                role == "tool"
                and isinstance(content, str)
                and len(content) > self._TOOL_RESULT_MAX
            ):
                entry["content"] = (
                    content[: self._TOOL_RESULT_MAX] + "\n... (truncated)"
                )
            history.append(entry)
        self._trim_history(history)

    def _trim_history(self, history: list[dict[str, Any]]) -> None:
        """Trim history to max_history, aligned to user turn boundaries."""
        if len(history) <= self.max_history:
            return
        tail = history[-self.max_history :]
        for i, m in enumerate(tail):
            if m.get("role") == "user":
                history[:] = tail[i:]
                return
        history[:] = tail

    async def _execute_tool(self, tc: ToolCallRequest) -> str:
        """Execute a tool call via MCP."""
        logger.debug(f"Executing tool: {tc.name}")
        try:
            result = await self.mcp.call_tool(tc.name, tc.arguments)
            if len(result) > self._TOOL_RESULT_INFERENCE_MAX:
                result = result[:self._TOOL_RESULT_INFERENCE_MAX] + "\n... (truncated)"
            return result
        except Exception as e:
            logger.exception("Tool execution failed: %s", tc.name)
            return "Tool execution failed. Please try a different approach."

    async def _send_response(
        self, msg: InboundMessage, content: str, *, progress: bool = False,
    ) -> None:
        """Send a response back to the channel."""
        metadata: dict[str, Any] = {"_progress": progress}
        reply_to_id = msg.metadata.get("message_id")
        if reply_to_id is not None:
            metadata["message_id"] = reply_to_id
        response = OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=content,
            metadata=metadata,
        )
        await self.bus.publish_outbound(response)
