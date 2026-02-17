"""
Unit tests for claw_swarm.replier.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from claw_swarm.gateway.schema import Platform
from claw_swarm.replier import send_message_async, send_message


class TestSendMessageAsync:
    """Test send_message_async with mocked aiohttp."""

    @pytest.mark.asyncio
    async def test_unsupported_platform_returns_false(self):
        ok, err = await send_message_async(
            Platform.UNSPECIFIED,
            "ch",
            "",
            "text",
        )
        assert ok is False
        assert "Unsupported" in err or "platform" in err.lower()

    @pytest.mark.asyncio
    async def test_telegram_missing_token_returns_false(self):
        with patch.dict(
            os.environ, {"TELEGRAM_BOT_TOKEN": ""}, clear=False
        ):
            ok, err = await send_message_async(
                Platform.TELEGRAM,
                "ch1",
                "",
                "Hello",
            )
        assert ok is False
        assert "TELEGRAM" in err or "missing" in err.lower()

    @pytest.mark.asyncio
    async def test_discord_missing_token_returns_false(self):
        with patch.dict(
            os.environ, {"DISCORD_BOT_TOKEN": ""}, clear=False
        ):
            ok, err = await send_message_async(
                Platform.DISCORD,
                "ch",
                "",
                "Hi",
            )
        assert ok is False
        assert "DISCORD" in err or "missing" in err.lower()

    @pytest.mark.asyncio
    async def test_whatsapp_missing_creds_returns_false(self):
        with patch.dict(
            os.environ,
            {
                "WHATSAPP_ACCESS_TOKEN": "",
                "WHATSAPP_PHONE_NUMBER_ID": "",
            },
            clear=False,
        ):
            ok, err = await send_message_async(
                Platform.WHATSAPP,
                "",
                "",
                "Hi",
            )
        assert ok is False
        assert "WHATSAPP" in err or "missing" in err.lower()

    @pytest.mark.asyncio
    async def test_whatsapp_missing_channel_and_thread_returns_false(
        self,
    ):
        with patch.dict(
            os.environ,
            {
                "WHATSAPP_ACCESS_TOKEN": "t",
                "WHATSAPP_PHONE_NUMBER_ID": "p",
            },
            clear=False,
        ):
            ok, err = await send_message_async(
                Platform.WHATSAPP,
                "",
                "",
                "Hi",
            )
        assert ok is False
        assert (
            "channel" in err.lower()
            or "recipient" in err.lower()
            or "wa_id" in err.lower()
        )


class TestSendMessageSync:
    """Test synchronous send_message wrapper."""

    def test_calls_async_and_returns_result(self):
        with patch(
            "claw_swarm.replier.send_message_async",
            new_callable=AsyncMock,
            return_value=(True, ""),
        ):
            ok, err = send_message(
                Platform.UNSPECIFIED, "ch", "", "t"
            )
        assert ok is True
        assert err == ""
