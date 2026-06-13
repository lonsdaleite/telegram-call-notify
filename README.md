# telegram-call-notify

Minimal Telethon userbot that listens for incoming Telegram calls and sends repeated notifications to [ntfy](https://ntfy.sh/) while the call is ringing.

Runs from any working directory under any Unix user. Config (`.env`) and session files are always resolved relative to `main.py`, not the current shell directory.

## Requirements

- Python 3.10+
- Unix-like server (Linux)
- Telegram API credentials from https://my.telegram.org
- Running ntfy instance (self-hosted or remote)

## Setup

Copy the project folder anywhere, for example `~/apps/telegram-call-notify`:

```bash
cd ~/apps/telegram-call-notify
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill TG_API_ID, TG_API_HASH, NTFY_URL
chmod 600 .env
```

## Run

From any directory:

```bash
~/apps/telegram-call-notify/.venv/bin/python ~/apps/telegram-call-notify/main.py
```

Or after `source .venv/bin/activate`:

```bash
python /path/to/telegram-call-notify/main.py
```

Debug mode (no ntfy, logs to console):

```bash
python /path/to/telegram-call-notify/main.py --debug
```

On first run, enter the Telegram login code. A `.session` file is created next to `main.py`.

Keep the process running with your preferred method (screen, tmux, nohup, etc.).

## Configuration

All settings are read from `.env` in the same directory as `main.py`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TG_API_ID` | yes | — | Telegram API ID |
| `TG_API_HASH` | yes | — | Telegram API hash |
| `TG_SESSION` | no | `userbot` | Session name or absolute path |
| `NTFY_URL` | prod | — | Full ntfy topic URL |
| `NTFY_TOKEN` | no | — | Bearer token for ntfy |
| `NOTIFY_COUNT` | no | `3` | Max notifications per call |
| `NOTIFY_INTERVAL` | no | `5` | Seconds between notifications |
| `NTFY_PRIORITY` | no | `high` | ntfy priority header |
| `DEBUG` | no | `false` | Local logging, no ntfy |

CLI flag `--debug` overrides `DEBUG` from `.env`.

## Behavior

- On incoming call (`PhoneCallRequested`): start sending notifications every `NOTIFY_INTERVAL` seconds, up to `NOTIFY_COUNT` times.
- On answer or hangup (`PhoneCallAccepted`, `PhoneCall`, `PhoneCallDiscarded`): stop immediately.
- Notification text: `Входящий звонок от {caller name}`.

## Security

- Never commit `.env` or `*.session` (see `.gitignore`).
- Keep `.env` and `*.session` readable only by your user: `chmod 600 .env *.session`.
- Session file = full account access.
- If compromised: Telegram → Settings → Privacy → Active Sessions → terminate all other sessions.

## License

MIT
