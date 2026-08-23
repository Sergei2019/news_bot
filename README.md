# Telegram News Aggregator Bot

Pulls headlines from RSS feeds + NewsAPI.org, filters/deduplicates them, and
posts new articles to your Telegram channel on a schedule.

## 1. Create your Telegram bot
1. Open Telegram, message **@BotFather**, send `/newbot`, follow the prompts.
2. Copy the token it gives you (looks like `123456789:AAExample...`).

## 2. Create/prepare your channel
1. Create a channel (or use an existing one).
2. Add your bot as an **admin** of the channel (Channel settings → Administrators → Add Admin).
3. If the channel is public, note its `@username`. If private, you'll need its
   numeric chat ID — forward any message from the channel to **@JsonDumpBot**
   or **@getidsbot** to get it (looks like `-1001234567890`).

## 3. Get a NewsAPI key (optional but recommended)
Free key at https://newsapi.org/register (100 requests/day on the free tier).
Set `newsapi.enabled: false` in `config.yaml` if you'd rather run RSS-only.

## 4. Configure
```bash
cp .env.example .env
# then edit .env with your bot token, channel ID, and NewsAPI key
```
Edit `config.yaml` to add/remove RSS feeds, change the polling interval, or
add keyword filters.

## 5. Install & run locally
```bash
pip install -r requirements.txt
python main.py
```
The bot will check for new articles immediately, then again every
`poll_interval_minutes` (default 60).

## 6. Deploy so it runs 24/7
Pick whichever you're most comfortable with:

- **Railway / Render** — create a "Background Worker" service, point it at
  this repo, set the same env vars from `.env` in their dashboard.
- **A VPS** — run it under `systemd` or inside `tmux`/`screen`, or use the
  included `Dockerfile`.
- **Docker**:
  ```bash
  docker build -t news-bot .
  docker run -d --env-file .env --name news-bot news-bot
  ```

## Notes
- Articles are deduped by URL in `seen_articles.db` (SQLite), so restarting
  the bot won't cause repeat posts.
- `max_posts_per_cycle` in `config.yaml` caps how many articles get posted
  per check, so a burst of new articles won't flood your channel.
- Want a different news API (GNews, NewsData.io, etc.)? Swap the logic in
  `fetch_newsapi()` inside `fetchers.py` — everything else stays the same.
