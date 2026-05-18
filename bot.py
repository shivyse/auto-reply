import os
import logging
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

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# --- Config ---
OFFLINE_MESSAGE = (
    "Hey! I'm currently offline but I'll get back to you as soon as I'm back. "
    "Leave your message and I'll reply soon! 🙏"
)

IS_ONLINE = False  # Set to True to disable auto-reply

ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")  # Your personal Telegram user ID


# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot is active! I'll auto-reply when the owner is offline."
    )


async def setonline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global IS_ONLINE
    if str(update.effective_user.id) == str(ADMIN_CHAT_ID):
        IS_ONLINE = True
        await update.message.reply_text("✅ You're now marked as ONLINE. Auto-reply disabled.")
    else:
        await update.message.reply_text("❌ You're not authorized.")


async def setoffline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global IS_ONLINE
    if str(update.effective_user.id) == str(ADMIN_CHAT_ID):
        IS_ONLINE = False
        await update.message.reply_text("💤 You're now marked as OFFLINE. Auto-reply enabled.")
    else:
        await update.message.reply_text("❌ You're not authorized.")


async def setmessage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global OFFLINE_MESSAGE
    if str(update.effective_user.id) == str(ADMIN_CHAT_ID):
        if context.args:
            OFFLINE_MESSAGE = " ".join(context.args)
            await update.message.reply_text(f"✅ Auto-reply message updated:\n\n{OFFLINE_MESSAGE}")
        else:
            await update.message.reply_text("Usage: /setmessage Your custom reply message here")
    else:
        await update.message.reply_text("❌ You're not authorized.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = "🟢 ONLINE" if IS_ONLINE else "🔴 OFFLINE (auto-reply ON)"
    await update.message.reply_text(
        f"Status: {state}\n\nAuto-reply message:\n{OFFLINE_MESSAGE}"
    )


async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if IS_ONLINE:
        return  # Don't reply if online

    user = update.effective_user
    if str(user.id) == str(ADMIN_CHAT_ID):
        return  # Don't reply to yourself

    logger.info(f"Message from {user.first_name} ({user.id}): {update.message.text}")
    await update.message.reply_text(OFFLINE_MESSAGE)


# --- Main ---

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("online", setonline))
    app.add_handler(CommandHandler("offline", setoffline))
    app.add_handler(CommandHandler("setmessage", setmessage))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    port = int(os.environ.get("PORT", 8443))
    webhook_url = os.environ.get("WEBHOOK_URL", "")

    if webhook_url:
        logger.info(f"Starting webhook on port {port}")
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
        )
    else:
        logger.info("No WEBHOOK_URL set, falling back to polling (for local testing)")
        app.run_polling()


if __name__ == "__main__":
    main()
