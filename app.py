#!/usr/bin/env python3
"""
TubePulse US - AI YouTube Automation Platform for US-Based Audiences
Web Dashboard, REST API, and CLI Engine.
"""

import os
import sys
import argparse
import logging
from flask import Flask, render_template, request, jsonify, send_file

from engine.us_intelligence import (
    US_NICHES,
    US_TREND_RADAR,
    US_HOOK_FORMULAS,
    US_POSTING_WINDOWS,
    get_current_us_times,
    get_next_optimal_upload_time,
)
from engine.script_engine import generate_youtube_script, analyze_script_retention
from engine.audio_engine import US_VOICES, ensure_default_audio
from engine.thumbnail_engine import generate_thumbnail, predict_ctr_score
from engine.video_engine import render_automated_video
from engine.seo_engine import generate_seo_package, calculate_us_revenue_projection
from engine.scheduler import (
    load_queue,
    save_queue,
    add_to_queue,
    update_item_status,
    create_export_package,
    simulate_youtube_api_upload,
)
from engine.curiosity_engine import (
    CURIOSITY_VAULT,
    get_random_curiosity_topic,
    generate_curiosity_script,
    analyze_curiosity_gap,
)
from engine.autopilot_engine import (
    load_channel_state,
    save_channel_state,
    run_autonomous_cycle,
    advance_channel_day,
    force_switch_phase,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TubePulseUS")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = "tubepulse-us-secret-2026"

# Ensure essential audio beds exist on startup
try:
    ensure_default_audio()
except Exception as e:
    logger.warning(f"Audio pre-generation warning: {e}")

@app.after_request
def add_header(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
    return response

# ----------------- WEB ROUTES -----------------

@app.route("/")
def index():
    return render_template("index.html")

# ----------------- API ENDPOINTS -----------------

@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify({
        "status": "online",
        "app": "TubePulse US",
        "version": "2.4.0",
        "audience": "United States (US-focused)",
        "us_times": get_current_us_times(),
        "next_upload_window": get_next_optimal_upload_time()
    })

@app.route("/api/us-intel", methods=["GET"])
def api_us_intel():
    return jsonify({
        "niches": US_NICHES,
        "trends": US_TREND_RADAR,
        "hooks": US_HOOK_FORMULAS,
        "posting_windows": US_POSTING_WINDOWS,
        "us_times": get_current_us_times(),
        "optimal_slot": get_next_optimal_upload_time()
    })

@app.route("/api/voices", methods=["GET"])
def api_voices():
    return jsonify({
        "voices": US_VOICES,
        "default_voice": "caleb_us"
    })

@app.route("/api/generate-script", methods=["POST"])
def api_generate_script():
    data = request.json or {}
    topic = data.get("topic", "The 2026 US Wealth Loophole")
    niche = data.get("niche", "finance")
    format_type = data.get("format", "shorts")
    hook_style = data.get("hook_style", "fomo")

    script_result = generate_youtube_script(topic, niche, format_type, hook_style)
    return jsonify(script_result)

@app.route("/api/generate-thumbnail", methods=["POST"])
def api_generate_thumbnail():
    data = request.json or {}
    topic = data.get("topic", "US Tax Loophole 2026")
    niche = data.get("niche", "finance")
    custom_badge = data.get("custom_badge")

    thumb_path = generate_thumbnail(topic, niche, custom_badge)
    filename = os.path.basename(thumb_path)
    ctr_data = predict_ctr_score(topic, custom_badge or "", niche)

    return jsonify({
        "status": "success",
        "thumbnail_url": f"/static/media/thumbnails/{filename}",
        "filename": filename,
        "ctr_analysis": ctr_data
    })

@app.route("/api/render-video", methods=["POST"])
def api_render_video():
    data = request.json or {}
    script_data = data.get("script_data")
    topic = data.get("topic", "US Wealth Strategy")
    niche = data.get("niche", "finance")
    format_type = data.get("format", "shorts")

    if not script_data:
        script_data = generate_youtube_script(topic, niche, format_type)

    video_result = render_automated_video(script_data, niche, format_type)
    return jsonify(video_result)

@app.route("/api/generate-seo", methods=["POST"])
def api_generate_seo():
    data = request.json or {}
    topic = data.get("topic", "US Wealth Strategy")
    niche = data.get("niche", "finance")
    format_type = data.get("format", "shorts")

    seo_pkg = generate_seo_package(topic, niche, format_type)
    rev_projection = calculate_us_revenue_projection(100000, niche)
    seo_pkg["revenue_projection_100k"] = rev_projection

    return jsonify(seo_pkg)

@app.route("/api/calculate-revenue", methods=["POST"])
def api_calculate_revenue():
    data = request.json or {}
    views = int(data.get("views", 100000))
    niche = data.get("niche", "finance")
    us_share = float(data.get("us_share", 0.75))

    rev = calculate_us_revenue_projection(views, niche, us_share)
    return jsonify(rev)

@app.route("/api/quick-automate", methods=["POST"])
def api_quick_automate():
    """
    End-to-end 1-Click Automation Pipeline:
    1. Generates US Script & Retention Analysis
    2. Renders 1280x720 High-CTR Thumbnail
    3. Renders MP4 Video with kinetic cards & audio bed
    4. Generates US SEO package & descriptions
    5. Packages all deliverables into downloadable ZIP
    6. Adds entry to US Content Publishing Queue
    """
    data = request.json or {}
    topic = data.get("topic", "The 2026 US Wealth Loophole").strip()
    niche = data.get("niche", "finance")
    format_type = data.get("format", "shorts")
    custom_badge = data.get("custom_badge")

    logger.info(f"Starting 1-Click Automation for: '{topic}' (Niche: {niche}, Format: {format_type})")

    # 1. Script
    script = generate_youtube_script(topic, niche, format_type)

    # 2. Thumbnail
    thumb_path = generate_thumbnail(topic, niche, custom_badge)
    thumb_filename = os.path.basename(thumb_path)
    thumb_url = f"/static/media/thumbnails/{thumb_filename}"
    ctr_analysis = predict_ctr_score(topic, custom_badge or "", niche)

    # 3. Video
    video_res = render_automated_video(script, niche, format_type)

    # 4. SEO
    seo = generate_seo_package(topic, niche, format_type)

    # 5. Add to queue
    queue_item = add_to_queue({
        "topic": topic,
        "niche": niche,
        "format": "Shorts (9:16)" if format_type == "shorts" else "Long-Form (16:9)",
        "title": seo["selected_title"],
        "video_url": video_res["url"],
        "thumbnail_url": thumb_url,
        "duration": f"{video_res['duration']}s",
        "projected_rpm": f"${US_NICHES.get(niche, {}).get('avg_rpm', 30.00):.2f}"
    })

    # 6. Package bundle
    zip_url = create_export_package(
        item_id=queue_item["id"],
        video_path=video_res["video_path"],
        thumb_path=thumb_path,
        script_text=script["full_text"],
        seo_data=seo
    )

    return jsonify({
        "status": "success",
        "queue_item": queue_item,
        "script": script,
        "thumbnail": {
            "url": thumb_url,
            "filename": thumb_filename,
            "ctr_analysis": ctr_analysis
        },
        "video": video_res,
        "seo": seo,
        "bundle_zip_url": zip_url,
        "message": "Full YouTube Automation asset package generated and scheduled successfully!"
    })

@app.route("/api/queue", methods=["GET"])
def api_get_queue():
    queue = load_queue()
    return jsonify({
        "queue": queue,
        "count": len(queue),
        "optimal_slot": get_next_optimal_upload_time()
    })

@app.route("/api/queue/publish", methods=["POST"])
def api_publish_queue_item():
    data = request.json or {}
    item_id = data.get("id")
    if not item_id:
        return jsonify({"error": "Item ID required"}), 400

    upload_result = simulate_youtube_api_upload({"title": data.get("title", "Video")})
    update_item_status(item_id, "Published")

    return jsonify({
        "status": "success",
        "upload_result": upload_result
    })

@app.route("/api/batch-generate", methods=["POST"])
def api_batch_generate():
    """Generates a multi-day US posting schedule batch automatically."""
    data = request.json or {}
    niche = data.get("niche", "finance")
    count = min(7, int(data.get("count", 3)))

    niche_data = US_NICHES.get(niche, US_NICHES["finance"])
    sample_topics = niche_data["sample_topics"][:count]

    created_items = []
    for topic in sample_topics:
        # Quick automated generation
        script = generate_youtube_script(topic, niche, "shorts")
        thumb_path = generate_thumbnail(topic, niche)
        thumb_filename = os.path.basename(thumb_path)
        video_res = render_automated_video(script, niche, "shorts")
        seo = generate_seo_package(topic, niche, "shorts")

        item = add_to_queue({
            "topic": topic,
            "niche": niche,
            "format": "Shorts (9:16)",
            "title": seo["selected_title"],
            "video_url": video_res["url"],
            "thumbnail_url": f"/static/media/thumbnails/{thumb_filename}",
            "duration": f"{video_res['duration']}s",
            "projected_rpm": f"${niche_data['avg_rpm']:.2f}"
        })
        created_items.append(item)

    return jsonify({
        "status": "success",
        "batch_count": len(created_items),
        "items": created_items
    })

# ----------------- AUTOPILOT & CURIOSITY ENDPOINTS -----------------

@app.route("/api/autopilot/status", methods=["GET"])
def api_autopilot_status():
    """Returns current channel growth phase, day, metrics, and activity log."""
    state = load_channel_state()
    return jsonify(state)

@app.route("/api/autopilot/run-cycle", methods=["POST"])
def api_autopilot_run_cycle():
    """Executes the daily autonomous cycle according to current phase."""
    res = run_autonomous_cycle()
    return jsonify(res)

@app.route("/api/autopilot/advance-day", methods=["POST"])
def api_autopilot_advance_day():
    """Advances channel day and produces the day's videos according to strategy."""
    res = advance_channel_day()
    return jsonify(res)

@app.route("/api/autopilot/switch-phase", methods=["POST"])
def api_autopilot_switch_phase():
    """Manually toggles or forces phase switch between Shorts-Only and Hybrid."""
    data = request.json or {}
    target = data.get("target_phase")
    state = force_switch_phase(target)
    return jsonify({"status": "success", "new_phase": state["current_phase"], "state": state})

@app.route("/api/autopilot/configure", methods=["POST"])
def api_autopilot_configure():
    """Configures days of shorts-only and subscriber thresholds."""
    data = request.json or {}
    state = load_channel_state()

    if "shorts_only_duration_days" in data:
        state["shorts_only_duration_days"] = int(data["shorts_only_duration_days"])
    if "switch_threshold_subs" in data:
        state["switch_threshold_subs"] = int(data["switch_threshold_subs"])
    if "autopilot_enabled" in data:
        state["autopilot_enabled"] = bool(data["autopilot_enabled"])

    save_channel_state(state)
    return jsonify({"status": "success", "state": state})

@app.route("/api/curiosity/topics", methods=["GET"])
def api_curiosity_topics():
    """Returns the curiosity vault topics with intrigue scores and formulas."""
    return jsonify({
        "topics": CURIOSITY_VAULT,
        "count": len(CURIOSITY_VAULT)
    })

@app.route("/api/curiosity/generate", methods=["POST"])
def api_curiosity_generate():
    """Generates an ultra-high curiosity video package from topic ID or random."""
    data = request.json or {}
    topic_id = data.get("topic_id")
    format_type = data.get("format", "shorts")

    topic_item = None
    if topic_id:
        for t in CURIOSITY_VAULT:
            if t["id"] == topic_id:
                topic_item = t
                break
    if not topic_item:
        topic_item = get_random_curiosity_topic()

    # Generate Curiosity script
    script = generate_curiosity_script(topic_item, format_type)
    thumb_path = generate_thumbnail(topic_item["topic"], topic_item.get("niche", "finance"), topic_item.get("default_badge"))
    thumb_filename = os.path.basename(thumb_path)
    video_res = render_automated_video(script, topic_item.get("niche", "finance"), format_type)
    seo = generate_seo_package(topic_item["topic"], topic_item.get("niche", "finance"), format_type)

    queue_item = add_to_queue({
        "topic": topic_item["topic"],
        "niche": topic_item.get("niche", "finance"),
        "format": "Shorts (9:16)" if format_type == "shorts" else "Long-Form (16:9)",
        "title": seo["selected_title"],
        "video_url": video_res["url"],
        "thumbnail_url": f"/static/media/thumbnails/{thumb_filename}",
        "duration": f"{video_res['duration']}s",
        "scheduled_slot_us": "Today at 12:00 PM EDT (US Lunch Peak)",
        "projected_rpm": "$32.00" if format_type != "shorts" else "$14.50"
    })

    zip_url = create_export_package(queue_item["id"], video_res["video_path"], thumb_path, script["full_text"], seo)

    return jsonify({
        "status": "success",
        "topic_item": topic_item,
        "script": script,
        "video": video_res,
        "thumbnail_url": f"/static/media/thumbnails/{thumb_filename}",
        "seo": seo,
        "queue_item": queue_item,
        "bundle_zip_url": zip_url
    })

# ----------------- CLI MODE -----------------

def run_cli():
    parser = argparse.ArgumentParser(description="TubePulse US - CLI YouTube Automation")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--topic", type=str, default="The 2026 US Wealth Loophole", help="Video topic")
    parser.add_argument("--niche", type=str, default="finance", choices=list(US_NICHES.keys()), help="US Niche")
    parser.add_argument("--format", type=str, default="shorts", choices=["shorts", "long_form"], help="Video format")
    parser.add_argument("--badge", type=str, default=None, help="Custom thumbnail badge")
    parser.add_argument("--port", type=int, default=5000, help="Web server port")

    args = parser.parse_args()

    if args.cli:
        print("="*60)
        print("🚀 TubePulse US - Autonomous YouTube Pipeline")
        print(f"Target Audience: United States Viewers")
        print(f"Topic: {args.topic}")
        print(f"Niche: {args.niche} (Avg US RPM: ${US_NICHES[args.niche]['avg_rpm']})")
        print(f"Format: {args.format}")
        print("="*60)

        print("[1/5] Generating US Hook & Retention Script...")
        script = generate_youtube_script(args.topic, args.niche, args.format)
        print(f"  ✓ Script ready ({script['analysis']['word_count']} words, Retention Score: {script['analysis']['retention_score']}/100)")

        print("[2/5] Synthesizing High-CTR 1280x720 Thumbnail...")
        thumb_path = generate_thumbnail(args.topic, args.niche, args.badge)
        print(f"  ✓ Thumbnail generated at: {thumb_path}")

        print("[3/5] Rendering 1080p MP4 Video with FFmpeg...")
        video_res = render_automated_video(script, args.niche, args.format)
        print(f"  ✓ Video encoded: {video_res['video_path']} ({video_res['size_mb']} MB, {video_res['duration']}s)")

        print("[4/5] Generating US SEO & Timestamps...")
        seo = generate_seo_package(args.topic, args.niche, args.format)
        print(f"  ✓ SEO Title: {seo['selected_title']}")

        print("[5/5] Packaging Deliverables into ZIP...")
        queue_item = add_to_queue({
            "topic": args.topic,
            "niche": args.niche,
            "format": args.format,
            "title": seo["selected_title"],
            "video_url": video_res["url"],
            "thumbnail_url": f"/static/media/thumbnails/{os.path.basename(thumb_path)}",
            "duration": f"{video_res['duration']}s"
        })
        zip_url = create_export_package(queue_item["id"], video_res["video_path"], thumb_path, script["full_text"], seo)
        print(f"  ✓ Package Bundle Ready: {zip_url}")
        print("="*60)
        print("🎉 YouTube Automation Job Completed Successfully!")
        return

    # Start Flask Web Server
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting TubePulse US Web Dashboard on http://0.0.0.0:{port}...")
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    run_cli()
