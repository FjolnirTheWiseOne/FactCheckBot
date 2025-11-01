# FactCheckBot — bot run & deploy guide

This file explains how to run the Telegram bot locally, and how to deploy it (Render background worker). It also documents how others can connect to the API.

Prerequisites
- Python 3.10+ (project used 3.12/3.13 during development)
- A virtualenv (recommended)
- A Telegram Bot token from BotFather

1) Run the bot locally

- Install dependencies in a virtualenv

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

- Create or edit `backend/.env` with these variables:

```ini
TELEGRAM_TOKEN=123456:ABCDEF-your-token-here
API_URL=https://factcheckbot.onrender.com   # or http://127.0.0.1:8000 for local testing
```

- Start the bot:

```bash
python -u backend/bot.py
```

You should see `Starting bot...`. Test the bot by sending `/start` then `/check https://example.com` on Telegram.

2) Test end-to-end locally

- Start backend in one terminal:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

- Point `API_URL` in `backend/.env` to `http://127.0.0.1:8000` and start the bot as above.

3) Deploying the bot on Render (background worker)

- Create a new "Background Worker" in Render.
- Set the Build Command to:

```
pip install -r backend/requirements.txt
```

- Set the Start Command to:

```
python -u backend/bot.py
```

- In that Render service's environment settings, add:
  - `TELEGRAM_TOKEN` — value from BotFather
  - `API_URL` — the public URL of your FastAPI backend (e.g. `https://factcheckbot.onrender.com`)

- Deploy. Check the instance logs for `Starting bot...` and for runtime prints.

4) How someone else can connect

A) Use the Telegram bot (recommended for non-developers)
- Give them the bot username (from BotFather), e.g., `@YourFactCheckBot`.
- They open Telegram, search the bot, click Start, and send a URL or `/check <url>`.

B) Call the HTTP API directly (for devs/automation)
- POST to `/check` with a JSON body: `{ "url": "https://example.com/article" }`
- Example curl:

```bash
curl -X POST https://factcheckbot.onrender.com/check \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

- Response will be JSON with `title`, `trust_score`, `verdict`, `reasons`, and more.

5) Security & notes
- Never commit `backend/.env` with the token. Use Render's environment settings or other secret stores.
- For production bots with many users, consider webhooks (fewer resource needs) instead of polling — but polling is easiest and works well on Render background workers.
- If you plan to let others use the raw API, consider rate-limiting and authentication (API keys) to prevent abuse.

If you'd like, I can add a small systemd service file example, a Dockerfile for the bot, or wire a Render background-worker manifest. Tell me which option you'd like next.