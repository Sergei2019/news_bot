"""Formats articles and posts them to a Telegram channel via the Bot API."""

import logging

import requests

logger = logging.getLogger(__name__)


def escape_html(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_message(article: dict) -> str:
    title = escape_html(article["title"])
    source = escape_html(article["source"])
    summary = escape_html(article["summary"])
    link = article["link"]

    msg = f"<b>{title}</b>\n\n"
    if summary:
        msg += f"{summary}\n\n"
    msg += f'📰 <i>{source}</i>\n🔗 <a href="{link}">Read more</a>'
    return msg


def send_to_channel(bot_token: str, channel_id: str, article: dict) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": format_message(article),
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, data=payload, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Failed to send message to Telegram: %s", e)
        return False
