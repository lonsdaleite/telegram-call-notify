#!/usr/bin/env python3
import argparse
import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import aiohttp
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import (
    PhoneCall,
    PhoneCallAccepted,
    PhoneCallDiscarded,
    PhoneCallRequested,
    UpdatePhoneCall,
)

APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env")

logger = logging.getLogger("tg-call-notify")


@dataclass
class Config:
    api_id: int
    api_hash: str
    session: str
    ntfy_url: str
    ntfy_token: str
    notify_count: int
    notify_interval: float
    ntfy_priority: str
    debug: bool
    session_path: Path


def resolve_session_path(name: str) -> Path:
    path = Path(name)
    if path.is_absolute():
        return path
    return APP_DIR / path


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def load_config(debug_flag: bool | None) -> Config:
    debug = debug_flag if debug_flag is not None else parse_bool(os.getenv("DEBUG"), False)

    api_id_raw = os.getenv("TG_API_ID", "").strip()
    api_hash = os.getenv("TG_API_HASH", "").strip()
    if not api_id_raw or not api_hash:
        raise SystemExit("TG_API_ID and TG_API_HASH are required")

    ntfy_url = os.getenv("NTFY_URL", "").strip()
    if not debug and not ntfy_url:
        raise SystemExit("NTFY_URL is required when DEBUG is false")

    session_name = os.getenv("TG_SESSION", "userbot").strip() or "userbot"

    return Config(
        api_id=int(api_id_raw),
        api_hash=api_hash,
        session=session_name,
        ntfy_url=ntfy_url,
        ntfy_token=os.getenv("NTFY_TOKEN", "").strip(),
        notify_count=max(1, int(os.getenv("NOTIFY_COUNT", "3"))),
        notify_interval=max(0.5, float(os.getenv("NOTIFY_INTERVAL", "5"))),
        ntfy_priority=os.getenv("NTFY_PRIORITY", "high").strip() or "high",
        debug=debug,
        session_path=resolve_session_path(session_name),
    )


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def resolve_caller_name(client: TelegramClient, user_id: int) -> str:
    try:
        entity = await client.get_entity(user_id)
        name = getattr(entity, "first_name", None) or getattr(entity, "title", None)
        if name and getattr(entity, "last_name", None):
            name = f"{name} {entity.last_name}"
        if name:
            return str(name)
    except Exception as exc:
        logger.debug("Failed to resolve caller name for %s: %s", user_id, exc)
    return str(user_id)


async def post_ntfy(cfg: Config, text: str, title: str) -> None:
    headers = {
        "Title": title,
        "Priority": cfg.ntfy_priority,
    }
    if cfg.ntfy_token:
        headers["Authorization"] = f"Bearer {cfg.ntfy_token}"

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(cfg.ntfy_url, data=text.encode("utf-8"), headers=headers) as resp:
            if resp.status >= 400:
                body = await resp.text()
                raise RuntimeError(f"ntfy returned {resp.status}: {body}")


async def send_notification(
    cfg: Config,
    text: str,
    title: str,
    attempt: int,
    total: int,
) -> None:
    if cfg.debug:
        logger.info("[DEBUG] notify %d/%d: %s", attempt, total, text)
        return

    await post_ntfy(cfg, text, title)
    logger.info("Sent notification %d/%d", attempt, total)


async def notify_loop(cfg: Config, caller_name: str, call_id: int) -> None:
    title = "Telegram call"
    text = f"Входящий звонок от {caller_name}"

    attempt = 0
    try:
        for attempt in range(1, cfg.notify_count + 1):
            await send_notification(cfg, text, title, attempt, cfg.notify_count)
            if attempt < cfg.notify_count:
                await asyncio.sleep(cfg.notify_interval)
    except asyncio.CancelledError:
        logger.info("Notify loop cancelled for call_id=%s after %d/%d", call_id, attempt, cfg.notify_count)
        raise


def call_state_label(call) -> str:
    return type(call).__name__


async def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram incoming call -> ntfy notifier")
    parser.add_argument(
        "--debug",
        action="store_true",
        default=None,
        help="Debug mode: log notifications locally, skip ntfy",
    )
    args = parser.parse_args()

    cfg = load_config(args.debug if args.debug else None)
    setup_logging(cfg.debug)

    if cfg.debug:
        logger.warning("DEBUG mode enabled — ntfy requests are disabled")

    logger.info("App dir: %s", APP_DIR)
    logger.info("Session: %s", cfg.session_path)

    active_tasks: dict[int, asyncio.Task] = {}

    client = TelegramClient(str(cfg.session_path), cfg.api_id, cfg.api_hash)

    @client.on(events.Raw)
    async def on_raw_update(update) -> None:
        if not isinstance(update, UpdatePhoneCall):
            return

        call = update.phone_call
        state = call_state_label(call)

        if cfg.debug:
            logger.debug("UpdatePhoneCall call_id=%s state=%s", getattr(call, "id", "?"), state)

        if isinstance(call, PhoneCallRequested):
            call_id = call.id
            if call_id in active_tasks:
                return

            caller_name = await resolve_caller_name(client, call.admin_id)
            logger.info(
                "Incoming call call_id=%s caller=%r (id=%s)",
                call_id,
                caller_name,
                call.admin_id,
            )

            task = asyncio.create_task(notify_loop(cfg, caller_name, call_id))
            active_tasks[call_id] = task

            def done_callback(t: asyncio.Task, cid: int = call_id) -> None:
                active_tasks.pop(cid, None)
                if t.cancelled():
                    return
                exc = t.exception()
                if exc:
                    logger.error("Notify loop failed for call_id=%s: %s", cid, exc)

            task.add_done_callback(done_callback)
            return

        if isinstance(call, (PhoneCallAccepted, PhoneCall, PhoneCallDiscarded)):
            call_id = call.id
            task = active_tasks.pop(call_id, None)
            if task:
                task.cancel()
                logger.info("Call ended call_id=%s state=%s — notifications stopped", call_id, state)

    await client.start()
    me = await client.get_me()
    logger.info("Logged in as %s (id=%s)", getattr(me, "username", None) or me.first_name, me.id)
    logger.info("Listening for incoming calls…")

    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
