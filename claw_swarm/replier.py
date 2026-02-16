"""
Send replies back to Telegram, Discord, or WhatsApp using platform APIs.
Uses the same env vars as the gateway adapters (TELEGRAM_BOT_TOKEN, etc.).
The agent calls this after processing a message so the user gets a response.
"""

from __future__ import annotations

import asyncio
import os

import aiohttp

from claw_swarm.gateway.schema import Platform


async def send_message_async(
    platform: Platform,
    channel_id: str,
    thread_id: str,
    text: str,
) -> tuple[bool, str]:
    """
    Asynchronously send a text message to the given channel/thread on the specified platform.

    Args:
        platform (Platform): Target platform to send message to (TELEGRAM, DISCORD, WHATSAPP, etc.).
        channel_id (str): Channel or recipient identifier (chat id, channel id, or wa_id).
        thread_id (str): Thread/message context for reply threading (optional for some platforms).
        text (str): The message text to send.

    Returns:
        tuple[bool, str]: (success, error_message). error_message is empty when success is True.
    """
    if platform == Platform.TELEGRAM:
        return await _send_telegram(channel_id, thread_id, text)
    if platform == Platform.DISCORD:
        return await _send_discord(channel_id, thread_id, text)
    if platform == Platform.WHATSAPP:
        return await _send_whatsapp(channel_id, thread_id, text)
    return False, f"Unsupported platform: {platform}"


def send_message(
    platform: Platform,
    channel_id: str,
    thread_id: str,
    text: str,
) -> tuple[bool, str]:
    """
    Synchronous wrapper for sending a text message. Runs the async send in an event loop.

    Args:
        platform (Platform): Target platform for the message.
        channel_id (str): Channel or recipient id.
        thread_id (str): Thread or message id (optional).
        text (str): Message payload.

    Returns:
        tuple[bool, str]: (success, error_message). error_message is empty when success is True.
    """
    return asyncio.get_event_loop().run_until_complete(
        send_message_async(platform, channel_id, thread_id, text)
    )


async def _send_telegram(
    channel_id: str, thread_id: str, text: str
) -> tuple[bool, str]:
    """
    Send a message to a Telegram chat using the Telegram Bot API.

    Args:
        channel_id (str): Telegram chat id.
        thread_id (str): Optional Telegram thread/message_thread_id for reply threads.
        text (str): The message text.

    Returns:
        tuple[bool, str]: (success, error_message). If sending fails, error_message includes the reason.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token or not channel_id:
        return False, "TELEGRAM_BOT_TOKEN or channel_id missing"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: dict = {"chat_id": channel_id, "text": text}
    if thread_id:
        payload["message_thread_id"] = (
            int(thread_id) if thread_id.isdigit() else thread_id
        )

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                body = await resp.text()
                return (
                    False,
                    f"Telegram API {resp.status}: {body[:500]}",
                )
            return True, ""


async def _send_discord(
    channel_id: str, thread_id: str, text: str
) -> tuple[bool, str]:
    """
    Send a message to a Discord channel using the Discord Bot API.

    Args:
        channel_id (str): Discord channel id where the message is sent.
        thread_id (str): Optional message id to reply in a thread or reference.
        text (str): The message text (truncated to 2000 chars for Discord).

    Returns:
        tuple[bool, str]: (success, error_message). If sending fails, error_message includes the reason.
    """
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token or not channel_id:
        return False, "DISCORD_BOT_TOKEN or channel_id missing"

    url = (
        f"https://discord.com/api/v10/channels/{channel_id}/messages"
    )
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }
    payload: dict = {"content": text[:2000]}  # Discord limit 2000
    if thread_id:
        payload["message_reference"] = {
            "channel_id": channel_id,
            "message_id": thread_id,
        }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, json=payload
        ) as resp:
            if resp.status not in (200, 201):
                body = await resp.text()
                return (
                    False,
                    f"Discord API {resp.status}: {body[:500]}",
                )
            return True, ""


async def _send_whatsapp(
    channel_id: str, thread_id: str, text: str
) -> tuple[bool, str]:
    """
    Send a message to a WhatsApp recipient using the WhatsApp Cloud API.

    Args:
        channel_id (str): WhatsApp recipient wa_id (phone number, without +) when replying.
        thread_id (str): Optional thread id (used if channel_id empty).
        text (str): Message text (truncated to 4096 chars for WhatsApp).

    Returns:
        tuple[bool, str]: (success, error_message). If sending fails, error_message includes the reason.
    """
    token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    if not token or not phone_number_id:
        return (
            False,
            "WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID missing",
        )

    to_wa_id = channel_id or thread_id
    if not to_wa_id:
        return (
            False,
            "WhatsApp requires channel_id (recipient wa_id) to send",
        )

    url = (
        f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_wa_id.lstrip("+"),
        "type": "text",
        "text": {"body": text[:4096]},
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, json=payload
        ) as resp:
            if resp.status not in (200, 201):
                body = await resp.text()
                return (
                    False,
                    f"WhatsApp API {resp.status}: {body[:500]}",
                )
            return True, ""
