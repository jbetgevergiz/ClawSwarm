"""
Unit tests for claw_swarm.gateway.adapters.base (MessageAdapter).
"""

from __future__ import annotations

import pytest

from claw_swarm.gateway.adapters.base import MessageAdapter
from claw_swarm.gateway.schema import UnifiedMessage, Platform


class ConcreteAdapter(MessageAdapter):
    """Concrete implementation for testing abstract interface."""

    def __init__(self, name: str = "test"):
        self._name = name
        self._messages: list[UnifiedMessage] = []

    @property
    def platform_name(self) -> str:
        return self._name

    async def fetch_messages(
        self,
        since_timestamp_utc_ms: int = 0,
        max_messages: int = 100,
    ) -> list[UnifiedMessage]:
        return self._messages


class TestMessageAdapter:
    """Test MessageAdapter interface."""

    def test_can_instantiate_concrete_adapter(self):
        adapter = ConcreteAdapter("myplatform")
        assert adapter.platform_name == "myplatform"

    @pytest.mark.asyncio
    async def test_fetch_messages_returns_list(self):
        adapter = ConcreteAdapter()
        result = await adapter.fetch_messages()
        assert result == []

    @pytest.mark.asyncio
    async def test_stream_messages_default_implementation(self):
        msg = UnifiedMessage(
            id="1",
            platform=Platform.TELEGRAM,
            channel_id="ch",
            sender_id="s",
            text="hi",
            timestamp_utc_ms=100,
        )
        adapter = ConcreteAdapter()
        adapter._messages = [msg]
        collected = []
        async for m in adapter.stream_messages():
            collected.append(m)
            if len(collected) >= 1:
                break
        assert len(collected) == 1
        assert collected[0].id == "1"
