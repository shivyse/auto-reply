"""
TubePulse US - Autonomous Channel Growth & Autopilot Engine
Manages autonomous topic selection, video generation, and the two-phase YouTube channel evolution:
Phase 1: Shorts-Only Blitz (Audience Acquisition, Days 1-5)
Phase 2: Hybrid Scale (Shorts + Long-Form High-RPM Videos, Day 6+)
"""

import os
import json
import logging
from datetime import datetime, timezone

from .curiosity_engine import CURIOSITY_VAULT, get_random_curiosity_topic, generate_curiosity_script
from .thumbnail_engine import generate_thumbnail
from .video_engine import render_automated_video
from .seo_engine import generate_seo_package
from .scheduler import add_to_queue, create_export_package

logger = logging.getLogger("TubePulseAutopilot")

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "media", "channel_state.json")

DEFAULT_STATE = {
    "channel_name": "TubePulse US - Curiosity & High-RPM Channel",
    "autopilot_enabled": True,
    "current_day": 1,
    "shorts_only_duration_days": 5,
    "current_phase": "SHORTS_BLITZ", # SHORTS_BLITZ or HYBRID_EXPANSION
    "audience_subscribers": 142,
    "audience_views": 18450,
    "switch_threshold_subs": 500,
    "total_videos_created": 3,
    "last_run_time": None,
    "used_topic_ids": ["cur-1"],
    "activity_log": [
        {
            "timestamp": "Day 1, 08:00 AM EDT",
            "type": "PHASE_START",
            "message": "Channel launched in Phase 1: Shorts-Only Blitz. Goal: Rapid subscriber acquisition via YouTube Shorts algorithmic velocity."
        }
    ]
}

def load_channel_state():
    """Loads channel state or creates default."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    save_channel_state(DEFAULT_STATE)
    return DEFAULT_STATE

def save_channel_state(state):
    """Persists channel growth state to disk."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def check_and_update_phase(state):
    """
    Evaluates whether the channel has graduated from Shorts-Only to Hybrid mode.
    Transition triggers:
    1. Day >= shorts_only_duration_days OR
    2. audience_subscribers >= switch_threshold_subs
    """
    days_threshold = state.get("shorts_only_duration_days", 5)
    subs_threshold = state.get("switch_threshold_subs", 500)
    current_day = state.get("current_day", 1)
    current_subs = state.get("audience_subscribers", 0)

    old_phase = state.get("current_phase", "SHORTS_BLITZ")

    if current_day > days_threshold or current_subs >= subs_threshold:
        state["current_phase"] = "HYBRID_EXPANSION"
        if old_phase != "HYBRID_EXPANSION":
            log_msg = f"🎉 AUDIENCE MILESTONE UNLOCKED! Switched from Shorts-Only to HYBRID EXPANSION (Shorts + Long-Form Videos). Target Day: {current_day}, Audience: {current_subs} subs."
            logger.info(log_msg)
            state["activity_log"].insert(0, {
                "timestamp": f"Day {current_day}, 12:00 PM EDT",
                "type": "PHASE_TRANSITION",
                "message": log_msg
            })
    else:
        state["current_phase"] = "SHORTS_BLITZ"

    return state

def run_autonomous_cycle(state=None):
    """
    Autonomous Execution Engine:
    1. Determines current phase (Shorts-Only vs Hybrid).
    2. Selects high-curiosity topic(s) autonomously.
    3. Produces video(s), thumbnails, SEO, and queues them.
    4. Simulates organic US audience growth and updates metrics.
    """
    if state is None:
        state = load_channel_state()

    state = check_and_update_phase(state)
    phase = state["current_phase"]
    day = state["current_day"]
    used_ids = state.get("used_topic_ids", [])

    created_items = []

    if phase == "SHORTS_BLITZ":
        # Phase 1: Upload 2 high-curiosity Shorts per cycle (Lunch & Primetime)
        logger.info(f"[Autopilot Day {day}] Phase 1 (Shorts-Only Blitz) executing...")
        
        # Pick topic
        topic_item = get_random_curiosity_topic(exclude_ids=used_ids)
        used_ids.append(topic_item["id"])
        state["used_topic_ids"] = used_ids

        # Produce Short 1
        script = generate_curiosity_script(topic_item, format_type="shorts")
        thumb_path = generate_thumbnail(topic_item["topic"], topic_item.get("niche", "finance"), topic_item.get("default_badge"))
        thumb_filename = os.path.basename(thumb_path)
        video_res = render_automated_video(script, topic_item.get("niche", "finance"), "shorts")
        seo = generate_seo_package(topic_item["topic"], topic_item.get("niche", "finance"), "shorts")

        queue_item = add_to_queue({
            "topic": topic_item["topic"],
            "niche": topic_item.get("niche", "finance"),
            "format": "Shorts (9:16)",
            "title": seo["selected_title"],
            "video_url": video_res["url"],
            "thumbnail_url": f"/static/media/thumbnails/{thumb_filename}",
            "duration": f"{video_res['duration']}s",
            "scheduled_slot_us": "Today at 12:00 PM EDT (US Lunch Peak)",
            "projected_rpm": "$14.50"
        })
        created_items.append(queue_item)

        # Audience gain simulation (Shorts viral gain: +45 to +110 subs, +4k to +9k views)
        sub_gain = 75 + (day * 15)
        view_gain = 6200 + (day * 1200)
        state["audience_subscribers"] += sub_gain
        state["audience_views"] += view_gain
        state["total_videos_created"] += 1

        state["activity_log"].insert(0, {
            "timestamp": f"Day {day}, 12:00 PM EDT",
            "type": "AUTO_SHORT_CREATED",
            "message": f"Autonomous Short Produced: '{topic_item['topic']}' (Curiosity: {topic_item['curiosity_score']}%). Audience gained: +{sub_gain} subs."
        })

    else:
        # Phase 2: HYBRID EXPANSION (1 Short + 1 Long-Form Deep Dive)
        logger.info(f"[Autopilot Day {day}] Phase 2 (Hybrid Scale) executing...")

        # 1. Produce 1 Short for top-of-funnel reach
        short_topic = get_random_curiosity_topic(exclude_ids=used_ids)
        used_ids.append(short_topic["id"])
        script_s = generate_curiosity_script(short_topic, format_type="shorts")
        thumb_s = generate_thumbnail(short_topic["topic"], short_topic.get("niche", "finance"), short_topic.get("default_badge"))
        video_s = render_automated_video(script_s, short_topic.get("niche", "finance"), "shorts")
        seo_s = generate_seo_package(short_topic["topic"], short_topic.get("niche", "finance"), "shorts")

        item_short = add_to_queue({
            "topic": short_topic["topic"],
            "niche": short_topic.get("niche", "finance"),
            "format": "Shorts (9:16)",
            "title": seo_s["selected_title"],
            "video_url": video_s["url"],
            "thumbnail_url": f"/static/media/thumbnails/{os.path.basename(thumb_s)}",
            "duration": f"{video_s['duration']}s",
            "scheduled_slot_us": "Today at 12:00 PM EDT (US Lunch Rush)",
            "projected_rpm": "$14.50"
        })
        created_items.append(item_short)

        # 2. Produce 1 Long-Form High-RPM Video (16:9)
        long_topic = get_random_curiosity_topic(exclude_ids=used_ids)
        used_ids.append(long_topic["id"])
        state["used_topic_ids"] = used_ids

        script_l = generate_curiosity_script(long_topic, format_type="long_form")
        thumb_l = generate_thumbnail(long_topic["topic"], long_topic.get("niche", "finance"), "DEEP DIVE EXPOSED")
        video_l = render_automated_video(script_l, long_topic.get("niche", "finance"), "long_form")
        seo_l = generate_seo_package(long_topic["topic"], long_topic.get("niche", "finance"), "long_form")

        item_long = add_to_queue({
            "topic": long_topic["topic"],
            "niche": long_topic.get("niche", "finance"),
            "format": "Long-Form (16:9)",
            "title": seo_l["selected_title"],
            "video_url": video_l["url"],
            "thumbnail_url": f"/static/media/thumbnails/{os.path.basename(thumb_l)}",
            "duration": f"{video_l['duration']}s",
            "scheduled_slot_us": "Today at 5:30 PM EDT (US Evening Primetime)",
            "projected_rpm": "$36.00"
        })
        created_items.append(item_long)

        # Higher subscriber & monetization gain from long-form
        sub_gain = 160 + (day * 20)
        view_gain = 18500 + (day * 3000)
        state["audience_subscribers"] += sub_gain
        state["audience_views"] += view_gain
        state["total_videos_created"] += 2

        state["activity_log"].insert(0, {
            "timestamp": f"Day {day}, 05:30 PM EDT",
            "type": "AUTO_HYBRID_CREATED",
            "message": f"Autonomous Hybrid Batch Produced: 1 Short ('{short_topic['topic']}') + 1 Long-Form Deep Dive ('{long_topic['topic']}'). Audience gained: +{sub_gain} subs."
        })

    state["last_run_time"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    state = check_and_update_phase(state)
    save_channel_state(state)

    return {
        "status": "success",
        "phase": state["current_phase"],
        "day": state["current_day"],
        "items_created": created_items,
        "audience": {
            "subscribers": state["audience_subscribers"],
            "views": state["audience_views"]
        },
        "state": state
    }

def advance_channel_day():
    """Simulates moving to the next day of channel growth and triggers daily creation."""
    state = load_channel_state()
    state["current_day"] += 1
    state = check_and_update_phase(state)
    save_channel_state(state)

    # Run production for the new day
    return run_autonomous_cycle(state)

def force_switch_phase(target_phase=None):
    """Allows manual override of phase (e.g. testing hybrid mode immediately)."""
    state = load_channel_state()
    if target_phase:
        state["current_phase"] = target_phase
    else:
        state["current_phase"] = "HYBRID_EXPANSION" if state["current_phase"] == "SHORTS_BLITZ" else "SHORTS_BLITZ"

    state["activity_log"].insert(0, {
        "timestamp": f"Day {state['current_day']}, Manual Action",
        "type": "MANUAL_PHASE_SWITCH",
        "message": f"Channel phase manually set to: {state['current_phase']}"
    })
    save_channel_state(state)
    return state
