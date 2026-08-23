"""Entry point. Runs forever, checking for new articles on a schedule
and posting any new ones to your Telegram channel.

Usage:
    python main.py
"""

import logging
import os
import time

import yaml
from dotenv import load_dotenv

import storage
from fetchers import fetch_rss, fetch_newsapi
from telegram_poster import send_to_channel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("news_bot")


def load_config(path="config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def passes_filters(article: dict, cfg: dict) -> bool:
    text = f"{article['title']} {article['summary']}".lower()

    blocked = [k.lower() for k in (cfg.get("blocked_keywords") or [])]
    if any(k in text for k in blocked):
        return False

    allowed = [k.lower() for k in (cfg.get("keyword_filters") or [])]
    if allowed and not any(k in text for k in allowed):
        return False

    return True


def run_cycle(cfg: dict, bot_token: str, channel_id: str, newsapi_key: str):
    all_articles = []
    all_articles.extend(fetch_rss(cfg.get("rss_feeds", [])))

    newsapi_cfg = cfg.get("newsapi", {})
    if newsapi_cfg.get("enabled"):
        all_articles.extend(fetch_newsapi(newsapi_key, newsapi_cfg))

    max_posts = cfg.get("max_posts_per_cycle", 5)
    new_count = 0

    for article in all_articles:
        if new_count >= max_posts:
            break
        if storage.has_seen(article["id"]):
            continue
        if not passes_filters(article, cfg):
            storage.mark_seen(article["id"])  # don't re-check filtered items every cycle
            continue

        if send_to_channel(bot_token, channel_id, article):
            logger.info("Posted: %s", article["title"])
            storage.mark_seen(article["id"])
            new_count += 1
            time.sleep(2)  # be gentle with Telegram's rate limits
        else:
            logger.warning("Skipped (send failed): %s", article["title"])

    logger.info(
        "Cycle complete. Posted %d new article(s) out of %d fetched.",
        new_count,
        len(all_articles),
    )


def main():
    load_dotenv()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
    newsapi_key = os.getenv("NEWSAPI_KEY", "")

    if not bot_token or not channel_id:
        raise SystemExit(
            "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID.\n"
            "Copy .env.example to .env and fill in your values."
        )

    cfg = load_config()
    storage.init_db()

    interval_seconds = cfg.get("poll_interval_minutes", 60) * 60
    logger.info("Starting news bot. Polling every %d minute(s).", interval_seconds // 60)

    while True:
        try:
            run_cycle(cfg, bot_token, channel_id, newsapi_key)
            storage.prune_old(days=30)
        except Exception as e:
            logger.exception("Error during cycle: %s", e)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
