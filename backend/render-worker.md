# Deploy the bot as a Render Background Worker (polling)

This file gives a copy/paste-ready checklist and recommended settings to host the polling bot on Render. It assumes your API is already deployed at `https://factcheckbot.onrender.com` (the web service defined in this repo).

Quick checklist (paste these into Render UI)

1) New Background Worker
- In Render dashboard click: New -> Background Worker
- Connect the GitHub repo and choose branch `dev`.

2) Build command
```
pip install -r backend/requirements.txt
```

3) Start command
```
python -u backend/bot.py
```

4) Environment variables (set in the Render service settings - Environment)
- `TELEGRAM_TOKEN` = <your-bot-token-from-BotFather>  (REQUIRED)
- `API_URL` = https://factcheckbot.onrender.com
- `PYTHONUNBUFFERED` = 1  (optional but recommended so logs stream immediately)

5) Instance & Scaling
- Choose the smallest instance that matches your traffic (Render free/cheap tier for low-traffic bots).
- Enable automatic restarts (default behaviour).

6) Verify logs
- After deploy, open Instance Logs. You should see `Starting bot...` from `backend/bot.py`.
- When users message the bot, you should see request/response logs or status in Render logs.

Notes & hardening
- Never store `TELEGRAM_TOKEN` in source code. Use Render's environment settings.
- If you expect many users consider switching to webhooks (lower resource usage). I can patch the repo to accept webhooks (one web service) if you want that next.
- If the bot fails to start, paste the Render logs here and I will diagnose. Common problems:
  - Missing dependency (pip install error) — check `backend/requirements.txt`.
  - `TELEGRAM_TOKEN` not set — bot exits with an error message.

Optional: Importing `render.yaml` into Render
- You can optionally import `render.yaml` from this repo into Render (Advanced → Import from repo). If Render asks for small schema changes, use the UI fields described above; the file is for convenience and automation-friendly workflows.

If you want, I can also:
- Add a small Dockerfile for the bot and a `render.yaml` variant that uses Docker.
- Modify the bot to run with webhooks and add the webhook endpoint to the FastAPI app so everything runs inside one web service.
