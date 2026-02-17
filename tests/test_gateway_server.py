"""
Unit tests for claw_swarm.gateway.server.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from claw_swarm.gateway.adapters.base import MessageAdapter
from claw_swarm.gateway.proto import messaging_gateway_pb2 as pb
from claw_swarm.gateway.schema import Platform, UnifiedMessage
from claw_swarm.gateway.server import (
    MessagingGatewayServicer,
    run_server,
)


class _FakeAdapter(MessageAdapter):
    """Minimal adapter for testing."""

    def __init__(
        self, platform_name: str, messages: list[UnifiedMessage]
    ):
        self._platform_name = platform_name
        self._messages = messages

    @property
    def platform_name(self) -> str:
        return self._platform_name

    async def fetch_messages(
        self,
        since_timestamp_utc_ms: int = 0,
        max_messages: int = 100,
    ) -> list[UnifiedMessage]:
        return self._messages


class TestMessagingGatewayServicer:
    """Test MessagingGatewayServicer."""

    @pytest.mark.asyncio
    async def test_health_returns_ok(self):
        servicer = MessagingGatewayServicer([], version="1.0")
        req = pb.HealthRequest()
        context = MagicMock()
        resp = await servicer.Health(req, context)
        assert resp.ok is True
        assert resp.version == "1.0"

    @pytest.mark.asyncio
    async def test_poll_messages_returns_from_adapter(self):
        msg = UnifiedMessage(
            id="m1",
            platform=Platform.TELEGRAM,
            channel_id="ch",
            sender_id="s",
            text="hello",
            timestamp_utc_ms=1000,
        )
        adapter = _FakeAdapter("telegram", [msg])
        servicer = MessagingGatewayServicer([adapter])
        req = pb.PollMessagesRequest(
            since_timestamp_utc_ms=0,
            max_messages=10,
        )
        context = MagicMock()
        resp = await servicer.PollMessages(req, context)
        assert len(resp.messages) == 1
        assert resp.messages[0].id == "m1"
        assert resp.messages[0].text == "hello"
        assert resp.messages[0].platform == pb.TELEGRAM

    @pytest.mark.asyncio
    async def test_poll_messages_sorts_by_timestamp(self):
        m1 = UnifiedMessage(
            id="a",
            platform=Platform.TELEGRAM,
            channel_id="ch",
            sender_id="s",
            timestamp_utc_ms=2000,
        )
        m2 = UnifiedMessage(
            id="b",
            platform=Platform.TELEGRAM,
            channel_id="ch",
            sender_id="s",
            timestamp_utc_ms=1000,
        )
        adapter = _FakeAdapter("telegram", [m1, m2])
        servicer = MessagingGatewayServicer([adapter])
        req = pb.PollMessagesRequest(
            since_timestamp_utc_ms=0, max_messages=10
        )
        context = MagicMock()
        resp = await servicer.PollMessages(req, context)
        assert len(resp.messages) == 2
        assert resp.messages[0].timestamp_utc_ms == 1000
        assert resp.messages[1].timestamp_utc_ms == 2000

    @pytest.mark.asyncio
    async def test_poll_messages_limits_max_messages(self):
        messages = [
            UnifiedMessage(
                id=f"m{i}",
                platform=Platform.TELEGRAM,
                channel_id="ch",
                sender_id="s",
                timestamp_utc_ms=1000 + i,
            )
            for i in range(5)
        ]
        adapter = _FakeAdapter("telegram", messages)
        servicer = MessagingGatewayServicer([adapter])
        req = pb.PollMessagesRequest(
            since_timestamp_utc_ms=0, max_messages=2
        )
        context = MagicMock()
        resp = await servicer.PollMessages(req, context)
        assert len(resp.messages) == 2

    @pytest.mark.asyncio
    async def test_adapters_by_platform_name(self):
        tg_msg = UnifiedMessage(
            id="t",
            platform=Platform.TELEGRAM,
            channel_id="ch",
            sender_id="s",
            timestamp_utc_ms=1,
        )
        dc_msg = UnifiedMessage(
            id="d",
            platform=Platform.DISCORD,
            channel_id="ch",
            sender_id="s",
            timestamp_utc_ms=2,
        )
        tg_adapter = _FakeAdapter("telegram", [tg_msg])
        dc_adapter = _FakeAdapter("discord", [dc_msg])
        servicer = MessagingGatewayServicer([tg_adapter, dc_adapter])
        req = pb.PollMessagesRequest(
            since_timestamp_utc_ms=0, max_messages=10
        )
        context = MagicMock()
        resp = await servicer.PollMessages(req, context)
        assert len(resp.messages) == 2
        ids = {m.id for m in resp.messages}
        assert ids == {"t", "d"}


class TestRunServer:
    """Test run_server."""

    @pytest.mark.asyncio
    async def test_starts_and_stops(self):
        adapter = _FakeAdapter("telegram", [])
        server = await run_server(
            [adapter],
            host="127.0.0.1",
            port=0,
        )
        try:
            assert server is not None
        finally:
            await server.stop(grace=None)
