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

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 8443))

OFFLINE_MESSAGE = (
    "Hey! I'm currently offline but I'll get back to you as soon as I'm back. "
    "Leave your message and I'll reply soon!"
)
IS_ONLINE = False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is active! I'll auto-reply when the owner is offline.")


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


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("online", setonline))
    app.add_handler(CommandHandler("offline", setoffline))
    app.add_handler(CommandHandler("setmessage", setmessage))
    app.add_handler(CommandHandler("status", status))
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
