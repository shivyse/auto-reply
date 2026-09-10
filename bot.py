import asyncio
import functools
import logging
import os
from clipper import whop_bot
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 8443))

# --- Clipping automation settings ---
CLIP_ALLOW_ALL = os.environ.get("CLIP_ALLOW_ALL", "") == "1"
WATCH_CHANNELS = [c.strip() for c in os.environ.get("WATCH_CHANNELS", "").split(",") if c.strip()]
WATCH_INTERVAL_MIN = int(os.environ.get("WATCH_INTERVAL_MIN", "15"))
WATCH_STATE_FILE = os.environ.get("WATCH_STATE_FILE", "clip_watch_state.json")
CLIP_LOCK = asyncio.Lock()

OFFLINE_MESSAGE = (
    "Hey! I'm currently offline but I'll get back to you as soon as I'm back. "
    "Leave your message and I'll reply soon!"
)
IS_ONLINE = False


# --------------------------------------------------------------------------- #
# existing auto-reply commands
# --------------------------------------------------------------------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot is active! I'll auto-reply when the owner is offline.\n\n"
        "🎬 Clipping: /clip <video-URL> [count] or just send me a video.\n"
        "Type /help for all commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Commands\n\n"
        "Auto-reply (admin):\n"
        "/online /offline — toggle auto-reply\n"
        "/setmessage <text> — set the offline reply\n"
        "/status — show current status\n\n"
        "🎬 Clipping:\n"
        "/clip <video-URL> [count] — auto-clip a video into vertical shorts\n"
        "   e.g. /clip https://youtu.be/xxxx 3\n"
        "Send a video file — clips it directly (max 50MB via Telegram,\n"
        "   larger files: send a link instead)\n\n"
        "Each clip comes back as a 9:16 captioned mp4 with a title + hashtags.\n\n"
        "💰 Whop clipping agent:\n"
        "/whop discover — find suitable paid campaigns\n"
        "/whop do <id> — produce compliant clips for a campaign\n"
        "/whop — all subcommands"
    )


async def setonline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global IS_ONLINE
    if str(update.effective_user.id) == str(ADMIN_CHAT_ID):
        IS_ONLINE = True
        await update.message.reply_text("You're now ONLINE. Auto-reply disabled.")
    else:
        await update.message.reply_text("Not authorized.")


async def setoffline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global IS_ONLINE
    if str(update.effective_user.id) == str(ADMIN_CHAT_ID):
        IS_ONLINE = False
        await update.message.reply_text("You're now OFFLINE. Auto-reply enabled.")
    else:
        await update.message.reply_text("Not authorized.")


async def setmessage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global OFFLINE_MESSAGE
    if str(update.effective_user.id) == str(ADMIN_CHAT_ID):
        if context.args:
            OFFLINE_MESSAGE = " ".join(context.args)
            await update.message.reply_text(f"Auto-reply message updated:\n\n{OFFLINE_MESSAGE}")
        else:
            await update.message.reply_text("Usage: /setmessage Your custom reply here")
    else:
        await update.message.reply_text("Not authorized.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = "ONLINE" if IS_ONLINE else "OFFLINE (auto-reply ON)"
    await update.message.reply_text(f"Status: {state}\n\nAuto-reply message:\n{OFFLINE_MESSAGE}")


async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if IS_ONLINE:
        return
    user = update.effective_user
    if str(user.id) == str(ADMIN_CHAT_ID):
        return
    await update.message.reply_text(OFFLINE_MESSAGE)


# --------------------------------------------------------------------------- #
# clipping automation
# --------------------------------------------------------------------------- #
def _clip_allowed(user_id) -> bool:
    return CLIP_ALLOW_ALL or str(user_id) == str(ADMIN_CHAT_ID)


def _clip_caption(clip: dict) -> str:
    parts = [clip.get("title", "Clip")]
    if clip.get("hook"):
        parts.append(f"\n“{clip['hook']}”")
    if clip.get("hashtags"):
        parts.append("\n" + " ".join(clip["hashtags"]))
    return "\n".join(parts)[:1000]


def _run_clip_job(**kwargs) -> dict:
    from clipper.config import ClipperConfig
    from clipper.pipeline import run_job

    cfg = ClipperConfig.from_env()
    return run_job(cfg=cfg, **kwargs)


async def _send_clips(target, clips: list[dict], context: ContextTypes.DEFAULT_TYPE,
                      reply_to=None):
    for clip in clips:
        caption = _clip_caption(clip)
        try:
            with open(clip["path"], "rb") as f:
                if reply_to is not None:
                    await reply_to.reply_video(video=f, caption=caption,
                                               supports_streaming=True)
                else:
                    await context.bot.send_video(chat_id=target, video=f,
                                                 caption=caption,
                                                 supports_streaming=True)
        except Exception as e:
            logger.warning("send clip failed: %s", e)
            text = f"⚠️ Couldn't send {clip.get('title')}: {e}"
            if reply_to is not None:
                await reply_to.reply_text(text)
            else:
                await context.bot.send_message(chat_id=target, text=text)


async def clip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _clip_allowed(update.effective_user.id):
        await update.message.reply_text("🔒 Clipping is admin-only on this bot.")
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: /clip <video-URL> [count]\n"
            "Example: /clip https://www.youtube.com/watch?v=xxxx 3"
        )
        return
    if CLIP_LOCK.locked():
        await update.message.reply_text("⏳ Busy rendering another clip job — try again shortly.")
        return
    url = context.args[0]
    try:
        count = int(context.args[1]) if len(context.args) > 1 else 3
    except ValueError:
        count = 3
    count = min(max(count, 1), 5)

    status_msg = await update.message.reply_text(
        f"⏳ Clipping your video…\n{url}\n\n"
        "Downloading → transcribing → finding viral moments → rendering."
    )
    async with CLIP_LOCK:
        try:
            result = await asyncio.to_thread(
                functools.partial(_run_clip_job, url=url, count=count))
        except Exception as e:
            logger.exception("clip job failed")
            await status_msg.edit_text(f"❌ Clip job failed:\n{e}")
            return
    clips = result.get("clips", [])
    await status_msg.edit_text(
        f"✅ Made {len(clips)} clip(s) from:\n{result['source'].get('title', url)}"
    )
    await _send_clips(None, clips, context, reply_to=update.message)


async def clip_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _clip_allowed(update.effective_user.id):
        return
    msg = update.message
    file_id, suffix = None, ".mp4"
    if msg.video:
        file_id = msg.video.file_id
    elif msg.document and (msg.document.mime_type or "").startswith("video/"):
        file_id = msg.document.file_id
        name = msg.document.file_name or ""
        if "." in name:
            suffix = "." + name.rsplit(".", 1)[-1][:5]
    else:
        return
    if CLIP_LOCK.locked():
        await msg.reply_text("⏳ Busy rendering another clip job — try again shortly.")
        return

    status_msg = await msg.reply_text("⏳ Got your video — finding the viral moments…")
    tmp_path = None
    async with CLIP_LOCK:
        try:
            import tempfile

            tg_file = await context.bot.get_file(file_id)
            fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix="clip_upload_")
            os.close(fd)
            await tg_file.download_to_drive(tmp_path)
            result = await asyncio.to_thread(
                functools.partial(_run_clip_job, file_path=tmp_path))
        except Exception as e:
            logger.exception("clip upload job failed")
            await status_msg.edit_text(f"❌ Clip job failed:\n{e}")
            return
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
    clips = result.get("clips", [])
    await status_msg.edit_text(f"✅ Made {len(clips)} clip(s) from your video.")
    await _send_clips(None, clips, context, reply_to=msg)


async def _maybe_autoupload(clips: list[dict]) -> list[str]:
    """Upload clips to YouTube Shorts if credentials are configured."""
    secrets = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")
    token = os.environ.get("YOUTUBE_TOKEN_FILE", "youtube_token.json")
    if not secrets or not os.path.exists(token):
        return []
    from clipper.uploader_youtube import upload_short

    privacy = os.environ.get("YOUTUBE_PRIVACY", "unlisted")
    links = []
    for clip in clips:
        try:
            url = await asyncio.to_thread(
                functools.partial(
                    upload_short, clip["path"], clip["title"],
                    description=f"{clip.get('hook', '')}\n\n{' '.join(clip.get('hashtags', []))}",
                    tags=[t.lstrip("#") for t in clip.get("hashtags", [])],
                    privacy=privacy, client_secrets=secrets, token_file=token))
            links.append(url)
        except Exception as e:
            logger.warning("youtube upload failed for %s: %s", clip.get("path"), e)
    return links


async def _watch_task(app):
    from clipper.watcher import watch_loop

    async def on_new(channel: str, video):
        await app.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"🎬 New upload on {channel}:\n{video.title}\n{video.url}\n\nClipping now…",
        )
        async with CLIP_LOCK:
            try:
                result = await asyncio.to_thread(
                    functools.partial(_run_clip_job, url=video.url))
            except Exception as e:
                logger.exception("auto-clip failed")
                await app.bot.send_message(
                    chat_id=ADMIN_CHAT_ID, text=f"❌ Auto-clip failed:\n{e}")
                return
        clips = result.get("clips", [])
        for clip in clips:
            caption = _clip_caption(clip)
            try:
                with open(clip["path"], "rb") as f:
                    await app.bot.send_video(chat_id=ADMIN_CHAT_ID, video=f,
                                             caption=caption,
                                             supports_streaming=True)
            except Exception as e:
                await app.bot.send_message(chat_id=ADMIN_CHAT_ID,
                                           text=f"⚠️ Couldn't send {clip.get('title')}: {e}")
        links = await _maybe_autoupload(clips)
        if links:
            await app.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text="📤 Uploaded to YouTube Shorts:\n" + "\n".join(links))

    await watch_loop(WATCH_CHANNELS, WATCH_STATE_FILE, WATCH_INTERVAL_MIN, on_new)


async def _post_init(app):
    if WATCH_CHANNELS and ADMIN_CHAT_ID:
        logger.info("Starting channel watcher for: %s", ", ".join(WATCH_CHANNELS))
        app.create_task(_watch_task(app))
    elif WATCH_CHANNELS:
        logger.warning("WATCH_CHANNELS set but ADMIN_CHAT_ID missing — watcher disabled.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(_post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("online", setonline))
    app.add_handler(CommandHandler("offline", setoffline))
    app.add_handler(CommandHandler("setmessage", setmessage))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("clip", clip_command))
    app.add_handler(CommandHandler("whop", functools.partial(
        whop_bot.wh_command, allow=_clip_allowed, lock=CLIP_LOCK,
        send_clips=_send_clips)))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL, clip_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    if WEBHOOK_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="",
            webhook_url=WEBHOOK_URL,
        )
    else:
        app.run_polling()


if __name__ == "__main__":
    main()
