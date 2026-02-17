"""
Unit tests for claw_swarm.gateway.schema (Platform, UnifiedMessage).
"""

from __future__ import annotations

import pytest

from claw_swarm.gateway.proto import messaging_gateway_pb2 as pb
from claw_swarm.gateway.schema import Platform, UnifiedMessage


class TestPlatform:
    """Test Platform enum."""

    def test_unspecified_is_zero(self):
        assert Platform.UNSPECIFIED == 0

    def test_telegram_discord_whatsapp_values(self):
        assert Platform.TELEGRAM == 1
        assert Platform.DISCORD == 2
        assert Platform.WHATSAPP == 3

    def test_from_int(self):
        assert Platform(0) == Platform.UNSPECIFIED
        assert Platform(1) == Platform.TELEGRAM


class TestUnifiedMessage:
    """Test UnifiedMessage model and gRPC roundtrip."""

    def test_minimal_message(self):
        msg = UnifiedMessage(
            id="id1",
            platform=Platform.TELEGRAM,
            channel_id="ch1",
            sender_id="s1",
        )
        assert msg.id == "id1"
        assert msg.platform == Platform.TELEGRAM
        assert msg.channel_id == "ch1"
        assert msg.thread_id == ""
        assert msg.sender_handle == ""
        assert msg.text == ""
        assert msg.attachment_urls == []
        assert msg.timestamp_utc_ms == 0
        assert msg.raw_metadata == b""

    def test_to_grpc(self):
        msg = UnifiedMessage(
            id="m1",
            platform=Platform.DISCORD,
            channel_id="c1",
            thread_id="t1",
            sender_id="s1",
            sender_handle="alice",
            text="hello",
            attachment_urls=["https://x.com/1"],
            timestamp_utc_ms=12345,
            raw_metadata=b"meta",
        )
        grpc_msg = msg.to_grpc()
        assert grpc_msg.id == "m1"
        assert grpc_msg.platform == 2  # DISCORD
        assert grpc_msg.channel_id == "c1"
        assert grpc_msg.thread_id == "t1"
        assert grpc_msg.sender_handle == "alice"
        assert grpc_msg.text == "hello"
        assert list(grpc_msg.attachment_urls) == ["https://x.com/1"]
        assert grpc_msg.timestamp_utc_ms == 12345
        assert grpc_msg.raw_metadata == b"meta"

    def test_from_grpc(self):
        grpc_msg = pb.UnifiedMessage(
            id="g1",
            platform=pb.TELEGRAM,
            channel_id="ch",
            thread_id="th",
            sender_id="sid",
            sender_handle="bob",
            text="hi",
            attachment_urls=["u1"],
            timestamp_utc_ms=999,
            raw_metadata=b"x",
        )
        msg = UnifiedMessage.from_grpc(grpc_msg)
        assert msg.id == "g1"
        assert msg.platform == Platform.TELEGRAM
        assert msg.channel_id == "ch"
        assert msg.thread_id == "th"
        assert msg.sender_handle == "bob"
        assert msg.text == "hi"
        assert msg.attachment_urls == ["u1"]
        assert msg.timestamp_utc_ms == 999
        assert msg.raw_metadata == b"x"

    def test_roundtrip_to_grpc_from_grpc(self):
        original = UnifiedMessage(
            id="r1",
            platform=Platform.WHATSAPP,
            channel_id="wa_ch",
            thread_id="",
            sender_id="wa_sender",
            sender_handle="+1234567890",
            text="Hello world",
            attachment_urls=[],
            timestamp_utc_ms=1000000,
            raw_metadata=b"",
        )
        grpc_msg = original.to_grpc()
        back = UnifiedMessage.from_grpc(grpc_msg)
        assert back.id == original.id
        assert back.platform == original.platform
        assert back.channel_id == original.channel_id
        assert back.sender_handle == original.sender_handle
        assert back.text == original.text
        assert back.timestamp_utc_ms == original.timestamp_utc_ms

    def test_extra_forbid_rejects_unknown_fields(self):
        with pytest.raises(
            Exception
        ):  # ValidationError from pydantic
            UnifiedMessage(
                id="x",
                platform=Platform.TELEGRAM,
                channel_id="c",
                sender_id="s",
                unknown_field="not allowed",
            )
