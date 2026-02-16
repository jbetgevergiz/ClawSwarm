"""
Telegram adapter: fetches messages via Bot API and normalizes to UnifiedMessage.
Configure with TELEGRAM_BOT_TOKEN env var; without it, fetch_messages returns [].
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import aiohttp
from loguru import logger

from claw_swarm.gateway.adapters.base import MessageAdapter
from claw_swarm.gateway.schema import Platform, UnifiedMessage

if TYPE_CHECKING:
    pass


class TelegramAdapter(MessageAdapter):
    """
    Adapter for fetching messages from Telegram using the Bot API.

    This class provides methods to poll Telegram for new messages via the "getUpdates" endpoint,
    normalize those messages into a consistent UnifiedMessage format, and enable downstream
    processing in the agent. It maintains an internal offset so only new messages are processed.

    Environment:
        - TELEGRAM_BOT_TOKEN: The Telegram Bot API token. Can be supplied explicitly via the constructor
          or set in the environment. If missing, no messages will be fetched.

    Features:
        - Polls Telegram using getUpdates to retrieve messages and channel posts.
        - Supports filtering by timestamp (`since_timestamp_utc_ms`) to fetch only new messages.
        - Limits the number of returned messages (`max_messages`, up to 100 per poll).
        - Extracts text and common attachments (photo, document, audio, voice, video) as file IDs.
        - Normalizes user info, channel, thread ID, attachments, and timestamp.

    Example usage:
        >>> adapter = TelegramAdapter(bot_token="...")
        >>> messages = await adapter.fetch_messages()
        for m in messages:
            print(m.text)

    Methods:
        - fetch_messages: Polls new updates and normalizes to UnifiedMessage.
        - platform_name: Returns "telegram".
    """

    def __init__(self, bot_token: str | None = None) -> None:
        self._token = bot_token or os.environ.get(
            "TELEGRAM_BOT_TOKEN"
        )
        self._offset: int | None = None

    @property
    def platform_name(self) -> str:
        return "telegram"

    async def fetch_messages(
        self,
        since_timestamp_utc_ms: int = 0,
        max_messages: int = 100,
    ) -> list[UnifiedMessage]:
        if not self._token:
            return []
        out: list[UnifiedMessage] = []
        url = f"https://api.telegram.org/bot{self._token}/getUpdates"
        params: dict = {
            "limit": min(max_messages, 100),
            "timeout": 10,
        }
        if self._offset is not None:
            params["offset"] = self._offset
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return out
                data = await resp.json()
        for u in data.get("result", []):
            self._offset = u["update_id"] + 1
            msg = u.get("message") or u.get("channel_post")
            if not msg:
                continue
            ts = msg.get("date", 0) * 1000
            if (
                since_timestamp_utc_ms
                and ts <= since_timestamp_utc_ms
            ):
                continue
            from_ = msg.get("from", {})
            chat = msg.get("chat", {})
            text = msg.get("text") or ""
            attachments: list[str] = []
            for key in (
                "photo",
                "document",
                "audio",
                "voice",
                "video",
            ):
                if key in msg:
                    # Telegram returns file_id; optional: resolve to URL via getFile
                    attachments.append(
                        msg[key][-1].get("file_id", "")
                        if isinstance(msg[key], list)
                        else str(msg[key])
                    )
            um = UnifiedMessage(
                id=str(msg["message_id"]),
                platform=Platform.TELEGRAM,
                channel_id=str(chat.get("id", "")),
                thread_id=str(chat.get("message_thread_id", "")),
                sender_id=str(from_.get("id", "")),
                sender_handle=from_.get("username", "")
                or from_.get("first_name", ""),
                text=text,
                attachment_urls=attachments,
                timestamp_utc_ms=ts,
            )
            out.append(um)
            logger.info(
                "[Message Received] platform=telegram channel_id={} sender_handle={} msg_id={} text_preview={!r}",
                um.channel_id,
                um.sender_handle,
                um.id,
                (
                    um.text[:80] + "..."
                    if len(um.text) > 80
                    else um.text
                ),
            )
            if len(out) >= max_messages:
                break
        return out
