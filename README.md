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
chmod +x start.sh stop.sh
```

## Run

### First login (interactive)

Run once in foreground to enter the Telegram code. A `.session` file is created next to `main.py`.

```bash
./start.sh
```

Or with debug (no ntfy):

```bash
./start.sh --debug
```

`--debug` can go before or after the log file:

```bash
./start.sh --debug /var/log/tg-call-notify.log
./start.sh /var/log/tg-call-notify.log --debug
```

### Background (daemon)

`start.sh` stops any existing instance, waits for `api.telegram.org:443`, activates `.venv` (or `venv`), then starts the service.

```bash
./start.sh /var/log/tg-call-notify.log
```

Stop:

```bash
./stop.sh
# or with the same log file:
./stop.sh /var/log/tg-call-notify.log
```

Without a log file argument, `start.sh` runs in foreground; with a log path it uses `nohup` and appends output to the file.

### Manual run

From any directory:

```bash
~/apps/telegram-call-notify/.venv/bin/python ~/apps/telegram-call-notify/main.py
```

Debug mode:

```bash
python /path/to/telegram-call-notify/main.py --debug
```

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

CLI flag `--debug` (in `main.py` or `./start.sh --debug`) overrides `DEBUG` from `.env`.

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
