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

from engine.us_intelligence import US_NICHES, US_TREND_RADAR, get_current_us_times, get_next_optimal_upload_time
from engine.script_engine import generate_youtube_script
from engine.thumbnail_engine import generate_thumbnail
from engine.video_engine import render_automated_video
from engine.seo_engine import generate_seo_package, calculate_us_revenue_projection
from engine.scheduler import add_to_queue, load_queue, create_export_package

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
    welcome_text = (
        "🚀 *TubePulse US - Autonomous YouTube Bot*\n\n"
        "Your channel automation assistant for high-RPM US audiences.\n\n"
        "*YouTube Automation Commands:*\n"
        "• `/generate <topic>` - Produce full video & thumbnail for US viewers\n"
        "• `/trends` - List top trending US keywords & RPMs\n"
        "• `/schedule` - Show scheduled US peak publishing queue\n"
        "• `/revenue <views>` - Calculate projected US AdSense & affiliate earnings\n"
        "• `/niches` - Show high-CPM US niches ($25 - $55 RPM)\n\n"
        "*Auto-Reply Commands:*\n"
        "• `/online` - Disable offline auto-reply\n"
        "• `/offline` - Enable offline auto-reply\n"
        "• `/status` - Bot and automation status\n"
        "• `/setmessage <text>` - Update auto-reply text"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args) if context.args else "The 2026 US Wealth Loophole"
    await update.message.reply_text(f"⏳ Generating full YouTube Automation package for US audience:\n\n*Topic:* {topic}\n*Target:* United States ($34.50 Avg RPM)\n\nPlease wait...", parse_mode="Markdown")

    try:
        script = generate_youtube_script(topic, "finance", "shorts")
        thumb_path = generate_thumbnail(topic, "finance")
        video_res = render_automated_video(script, "finance", "shorts")
        seo = generate_seo_package(topic, "finance", "shorts")

        item = add_to_queue({
            "topic": topic,
            "niche": "finance",
            "format": "Shorts (9:16)",
            "title": seo["selected_title"],
            "video_url": video_res["url"],
            "thumbnail_url": f"/static/media/thumbnails/{os.path.basename(thumb_path)}",
            "duration": f"{video_res['duration']}s",
            "projected_rpm": "$34.50"
        })

        reply_msg = (
            f"✅ *YouTube Video Automation Complete!*\n\n"
            f"🎬 *Title:* {seo['selected_title']}\n"
            f"📈 *US Retention Score:* {script['analysis']['retention_score']}%\n"
            f"⏱️ *Duration:* {video_res['duration']}s (Shorts 9:16)\n"
            f"📅 *Scheduled Slot:* {item['scheduled_slot_us']}\n\n"
            f"📁 *Deliverables Rendered:*\n"
            f"• 1080p MP4 Video ({video_res['size_mb']} MB)\n"
            f"• 1280x720 High-CTR Thumbnail\n"
            f"• Full YouTube Description & Tags\n"
            f"• Queued for peak US upload!"
        )
        await update.message.reply_text(reply_msg, parse_mode="Markdown")

        # Send thumbnail preview if file exists
        if os.path.exists(thumb_path):
            with open(thumb_path, "rb") as photo:
                await update.message.reply_photo(photo=photo, caption=f"Thumbnail for: {topic}")

    except Exception as e:
        logger.exception("Error in /generate:")
        await update.message.reply_text(f"❌ Generation error: {str(e)}")


async def trends_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🔥 *Top High-RPM US YouTube Trends (2026):*\n\n"
    for idx, t in enumerate(US_TREND_RADAR[:5], 1):
        msg += f"{idx}. *{t['topic']}*\n"
        msg += f"   • Niche: `{t['niche']}` | Vol: {t['search_volume']}\n"
        msg += f"   • RPM: *{t['projected_rpm']}* | Trend Score: {t['trend_score']}/100\n\n"
    msg += "Type `/generate <topic>` to create any of these instantly."
    await update.message.reply_text(msg, parse_mode="Markdown")


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    queue = load_queue()
    optimal = get_next_optimal_upload_time()
    us_times = get_current_us_times()

    msg = f"📅 *US Publishing Pipeline:*\n"
    msg += f"• Current EST: `{us_times['EST']}`\n"
    msg += f"• Next Peak Window: *{optimal['recommended_slot']}*\n\n"

    if not queue:
        msg += "No videos in queue. Use `/generate <topic>` to queue one!"
    else:
        msg += f"*Queued Videos ({len(queue)}):*\n"
        for idx, item in enumerate(queue[:4], 1):
            msg += f"{idx}. *{item.get('title', item['topic'])}*\n"
            msg += f"   Slot: `{item.get('scheduled_slot_us')}` | Status: `{item.get('status')}`\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def revenue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    views = 100000
    if context.args:
        try:
            views = int(context.args[0].replace(",", "").replace("k", "000").replace("m", "000000"))
        except ValueError:
            views = 100000

    rev = calculate_us_revenue_projection(views, "finance", 0.75)
    msg = (
        f"💰 *US YouTube Revenue Projection ({views:,} Views):*\n\n"
        f"• US Audience Share: *{rev['us_audience_share']}*\n"
        f"• Blended RPM: *{rev['blended_rpm']}*\n"
        f"• AdSense Revenue: *{rev['adsense_revenue']}*\n"
        f"• Sponsorships: *{rev['sponsorship_revenue']}*\n"
        f"• Affiliates: *{rev['affiliate_revenue']}*\n\n"
        f"🚀 *Total Estimated Revenue: {rev['total_projected_usd']}*"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def niches_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "💎 *Top Paying US YouTube Niches:*\n\n"
    for n in US_NICHES.values():
        msg += f"• *{n['name']}* ({n['badge']})\n"
        msg += f"  Avg US RPM: *${n['avg_rpm']:.2f}* ({n['rpm_range']})\n"
        msg += f"  Top States: {', '.join(n['top_us_states'][:3])}\n\n"
    await update.message.reply_text(msg, parse_mode="Markdown")


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
    us_times = get_current_us_times()
    optimal = get_next_optimal_upload_time()
    queue = load_queue()

    msg = (
        f"📊 *TubePulse US Bot Status*\n\n"
        f"• Auto-Reply State: *{state}*\n"
        f"• Current EST Time: `{us_times['EST']}`\n"
        f"• Next Optimal Upload: `{optimal['recommended_slot']}`\n"
        f"• Queued Videos: *{len(queue)}*\n\n"
        f"Auto-reply message:\n_{OFFLINE_MESSAGE}_"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if IS_ONLINE:
        return
    user = update.effective_user
    if str(user.id) == str(ADMIN_CHAT_ID):
        return
    await update.message.reply_text(OFFLINE_MESSAGE)


def main():
    if not BOT_TOKEN:
        logger.info("BOT_TOKEN not configured. Run app.py for the Web Dashboard and CLI.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # YouTube Automation Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_command))
    app.add_handler(CommandHandler("trends", trends_command))
    app.add_handler(CommandHandler("schedule", schedule_command))
    app.add_handler(CommandHandler("revenue", revenue_command))
    app.add_handler(CommandHandler("niches", niches_command))

    # Auto-reply Handlers
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
