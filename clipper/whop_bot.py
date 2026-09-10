"""Telegram /whop commands — Whop Content Rewards clipping agent.

Subcommands:
  discover            find suitable live campaigns
  show <n|url>        campaign details, payouts, rules, references
  add <url> [src...]  track a campaign (+ optional footage sources)
  source <id> <urls>  add footage URLs (creator videos/channels)
  rules <id> <text>   save full rules pasted from inside Whop
  do <id> [count]     fulfill: produce compliant ready-to-post clips
  posted <clip> <url> mark a clip posted (tracks your submissions)
  submitted <clip>    mark a clip submitted on Whop
  list                tracked campaigns + progress
"""
from __future__ import annotations

import asyncio
import functools

from telegram import Update
from telegram.ext import ContextTypes

HELP = (
    "🎬 /whop — Whop clipping agent\n\n"
    "/whop discover — find suitable paid campaigns\n"
    "/whop show <n|url> — payouts, rules, references\n"
    "/whop add <campaign-url> — track one you joined\n"
    "/whop source <id> <video-url> — add footage to clip\n"
    "/whop rules <id> <text> — save full rules from Whop\n"
    "/whop do <id> [count] — make ready-to-post clips\n"
    "/whop posted <clip-id> <post-url> — track posting\n"
    "/whop submitted <clip-id> — track Whop submission\n"
    "/whop list — tracked campaigns + progress"
)


async def _reply_long(message, text: str, limit: int = 3500):
    text = text.strip() or "(empty)"
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        cut = cut if cut > 0 else limit
        await message.reply_text(text[:cut])
        text = text[cut:].strip()
    await message.reply_text(text)


async def wh_command(update: Update, context: ContextTypes.DEFAULT_TYPE, *,
                     allow, lock, send_clips):
    from clipper.whop import (WhopPrefs, campaign_card, discover, fetch_campaign,
                              fulfill, get_campaign, load_curated, load_state,
                              parse_rules, resolve_ref, save_state, suitable,
                              upsert_campaign)

    if not allow(update.effective_user.id):
        await update.message.reply_text("🔒 Clipping is admin-only on this bot.")
        return
    args = list(context.args or [])
    sub = args.pop(0).lower() if args else "help"
    prefs = WhopPrefs.from_env()

    if sub == "discover":
        msg = await update.message.reply_text("🔍 Scanning Whop Content Rewards…")

        def _scan():
            st = load_state(prefs.state_file)
            cards = discover(limit=15, enrich=8)
            for c in cards:
                upsert_campaign(st, c)
            import os as _os
            for c in load_curated(_os.environ.get("WHOP_CAMPAIGNS_FILE", "")):
                upsert_campaign(st, c)
            good = suitable(cards, prefs)
            st["last_discover"] = [c.id for c in good]
            save_state(st, prefs.state_file)
            return good, cards

        try:
            good, cards = await asyncio.to_thread(_scan)
        except Exception as e:
            await msg.edit_text(f"❌ Discover failed:\n{e}")
            return
        if not good:
            await msg.edit_text(
                f"Found {len(cards)} campaigns, none match your filters "
                f"(min ${prefs.min_rate}/1k, ${prefs.min_budget_left:,.0f} left). "
                "Loosen WHOP_MIN_RATE / WHOP_MIN_BUDGET_LEFT.")
            return
        await msg.edit_text(f"✅ {len(good)} suitable campaign(s):")
        for i, c in enumerate(good[:8], 1):
            await update.message.reply_text(campaign_card(c, i))
        await update.message.reply_text("Details: /whop show <n>")

    elif sub == "show":
        if not args:
            await update.message.reply_text("Usage: /whop show <n|url|id>")
            return
        state = load_state(prefs.state_file)
        cid = resolve_ref(state, args[0])
        camp = get_campaign(state, cid) if cid else None
        if args[0].startswith("http") and (not camp or not camp.title):
            msg = await update.message.reply_text("⏳ Fetching campaign…")
            try:
                camp = await asyncio.to_thread(fetch_campaign, args[0])
            except Exception as e:
                await msg.edit_text(f"❌ Fetch failed:\n{e}")
                return
            upsert_campaign(state, camp)
            save_state(state, prefs.state_file)
            await msg.delete()
        if not camp:
            await update.message.reply_text(f"Unknown campaign: {args[0]}")
            return
        text = campaign_card(camp)
        if camp.description:
            text += f"\n\n{camp.description[:1200]}"
        rules = parse_rules(f"{camp.description}\n{camp.rules_text}")
        bits = []
        if rules["hashtags"] or rules["mentions"]:
            bits.append("#️⃣ " + " ".join(rules["hashtags"] + rules["mentions"]))
        if rules["min_len"] or rules["max_len"]:
            bits.append(f"⏱️ length: {rules['min_len'] or '?'}–{rules['max_len'] or '?'}s")
        for b in rules["banned"][:5]:
            bits.append(f"⚠️ {b}")
        if bits:
            text += "\n\n" + "\n".join(bits)
        if camp.reference_links:
            text += "\n\n📎 Reference:"
            for r in camp.reference_links[:6]:
                text += f"\n• {r['label']}: {r['url']}"
        if camp.sources:
            text += "\n\n🎞️ Sources:"
            for s in camp.sources[:6]:
                text += f"\n• {s}"
        else:
            text += ("\n\n🎞️ No footage sources yet — add with:\n"
                     f"/whop source {camp.id[:8]} <youtube-url>")
        if camp.join_url:
            text += f"\n\n➡️ Join/submit: {camp.join_url}"
        await _reply_long(update.message, text)

    elif sub == "add":
        if not args:
            await update.message.reply_text("Usage: /whop add <campaign-url> [source-url …]")
            return
        url, srcs = args[0], args[1:]
        msg = await update.message.reply_text("⏳ Tracking campaign…")
        try:
            camp = await asyncio.to_thread(fetch_campaign, url)
        except Exception as e:
            await msg.edit_text(f"❌ Fetch failed:\n{e}")
            return
        camp.status = "joined"
        camp.sources = srcs
        state = load_state(prefs.state_file)
        upsert_campaign(state, camp)
        save_state(state, prefs.state_file)
        await msg.edit_text(f"✅ Tracking: {camp.title or camp.id}\n"
                            f"ID: {camp.id[:8]} · {len(srcs)} source(s)")

    elif sub == "source":
        if len(args) < 2:
            await update.message.reply_text("Usage: /whop source <id> <video-url> […]")
            return
        state = load_state(prefs.state_file)
        cid = resolve_ref(state, args[0])
        camp = get_campaign(state, cid) if cid else None
        if not camp:
            await update.message.reply_text(f"Unknown campaign: {args[0]}")
            return
        camp.sources.extend(u for u in args[1:] if u not in camp.sources)
        upsert_campaign(state, camp)
        save_state(state, prefs.state_file)
        await update.message.reply_text(
            f"🎞️ {camp.title or cid}: {len(camp.sources)} source(s)")

    elif sub == "rules":
        if len(args) < 2:
            await update.message.reply_text("Usage: /whop rules <id> <full rules text…>")
            return
        state = load_state(prefs.state_file)
        cid = resolve_ref(state, args[0])
        camp = get_campaign(state, cid) if cid else None
        if not camp:
            await update.message.reply_text(f"Unknown campaign: {args[0]}")
            return
        camp.rules_text = " ".join(args[1:])
        r = parse_rules(camp.rules_text)
        camp.hashtags = sorted(set(camp.hashtags + r["hashtags"]))
        upsert_campaign(state, camp)
        save_state(state, prefs.state_file)
        await update.message.reply_text(
            f"📜 Rules saved ({len(r['hashtags'])} hashtags, "
            f"{len(r['banned'])} warnings, "
            f"length {r['min_len'] or '?'}–{r['max_len'] or '?'}s)")

    elif sub == "do":
        if not args:
            await update.message.reply_text("Usage: /whop do <id> [count]")
            return
        if lock.locked():
            await update.message.reply_text("⏳ Busy rendering another job — try again shortly.")
            return
        state = load_state(prefs.state_file)
        cid = resolve_ref(state, args[0])
        if not cid or not get_campaign(state, cid):
            await update.message.reply_text(
                f"Unknown campaign: {args[0]} (see /whop list)")
            return
        try:
            count = int(args[1]) if len(args) > 1 else None
        except ValueError:
            count = None
        msg = await update.message.reply_text("⏳ Fulfilling campaign — producing clips…")
        async with lock:
            try:
                res = await asyncio.to_thread(
                    functools.partial(fulfill, cid, prefs, count=count))
            except Exception as e:
                await msg.edit_text(f"❌ Fulfill failed:\n{e}")
                return
        clips = res["clips"]
        await msg.edit_text(f"✅ {len(clips)} compliant clip(s) ready.")
        for clip in clips:
            cap = (f"{clip.get('title', 'Clip')}\n\n{' '.join(clip.get('hashtags', []))}"
                   .strip()[:1000])
            try:
                with open(clip["path"], "rb") as f:
                    await update.message.reply_video(video=f, caption=cap,
                                                     supports_streaming=True)
            except Exception as e:
                await update.message.reply_text(f"⚠️ Couldn't send clip: {e}")
        await _reply_long(update.message, res["checklist"])

    elif sub in ("posted", "submitted"):
        if not args:
            await update.message.reply_text(f"Usage: /whop {sub} <clip-id> [post-url]")
            return
        state = load_state(prefs.state_file)
        found = None
        for c_id, d in state["campaigns"].items():
            for clip in d.get("clips", []):
                if clip.get("clip_id") == args[0]:
                    found = (c_id, clip)
        if not found:
            await update.message.reply_text(f"Unknown clip: {args[0]}")
            return
        _cid, clip = found
        if len(args) > 1:
            clip["post_url"] = args[1]
        clip["status"] = "submitted" if sub == "submitted" else "posted"
        save_state(state, prefs.state_file)
        await update.message.reply_text(f"✅ {args[0]} → {clip['status']}")

    elif sub == "list":
        state = load_state(prefs.state_file)
        if not state["campaigns"]:
            await update.message.reply_text(
                "Nothing tracked yet. Run /whop discover first.")
            return
        lines = []
        for c_id, d in state["campaigns"].items():
            clips = d.get("clips", [])
            n_post = sum(1 for x in clips if x.get("status") in ("posted", "submitted"))
            lines.append(
                f"• {d.get('title') or c_id[:8]} [{d.get('status')}] "
                f"${d.get('rate_per_1k', 0)}/1k\n"
                f"  id {c_id[:8]} · {len(d.get('sources', []))} sources · "
                f"{len(clips)} clips ({n_post} posted)")
        await _reply_long(update.message, "🎬 Tracked campaigns:\n\n" + "\n".join(lines))

    else:
        await update.message.reply_text(HELP)
