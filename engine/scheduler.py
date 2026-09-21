"""
TubePulse US - Content Scheduler & Automation Queue
Manages scheduled publishing across US timezones, batch creation, packaging zip downloads,
and YouTube Data API v3 publishing integration.
"""

import os
import json
import zipfile
import uuid
from datetime import datetime, timezone, timedelta
from .us_intelligence import get_next_optimal_upload_time, get_current_us_times

QUEUE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "media", "queue.json")
PACKAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "media", "packages")
os.makedirs(PACKAGE_DIR, exist_ok=True)

def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_queue(queue):
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)

def add_to_queue(item_data: dict) -> dict:
    """Adds a generated video item to the US publishing queue."""
    queue = load_queue()
    item_id = str(uuid.uuid4())[:8]

    # Calculate scheduled time if not provided
    optimal = get_next_optimal_upload_time()
    us_times = get_current_us_times()

    entry = {
        "id": item_id,
        "topic": item_data.get("topic", "Untitled Video"),
        "niche": item_data.get("niche", "finance"),
        "format": item_data.get("format", "Shorts (9:16)"),
        "title": item_data.get("title", item_data.get("topic", "")),
        "video_url": item_data.get("video_url", ""),
        "thumbnail_url": item_data.get("thumbnail_url", ""),
        "duration": item_data.get("duration", "30s"),
        "scheduled_slot_us": item_data.get("scheduled_slot_us", optimal["recommended_slot"]),
        "status": "Scheduled", # Scheduled, Published, Processing
        "created_at_us": us_times["EST"],
        "projected_rpm": item_data.get("projected_rpm", "$34.50"),
        "youtube_video_id": f"yt_us_{item_id}"
    }

    queue.insert(0, entry)
    save_queue(queue)
    return entry

def update_item_status(item_id: str, new_status: str):
    queue = load_queue()
    for item in queue:
        if item["id"] == item_id:
            item["status"] = new_status
            break
    save_queue(queue)
    return queue

def create_export_package(item_id: str, video_path: str, thumb_path: str, script_text: str, seo_data: dict) -> str:
    """
    Creates a complete downloadable ZIP package containing:
    1. MP4 Video (1080p ready to upload)
    2. PNG Thumbnail (1280x720 high CTR)
    3. METADATA_YOUTUBE.txt (Formatted titles, description, tags, hashtags, pinned comment)
    4. SCRIPT_VOICEOVER.txt (Full script with cues)
    """
    zip_filename = f"tubepulse_us_bundle_{item_id}.zip"
    zip_path = os.path.join(PACKAGE_DIR, zip_filename)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        if video_path and os.path.exists(video_path):
            z.write(video_path, arcname=os.path.basename(video_path))

        if thumb_path and os.path.exists(thumb_path):
            z.write(thumb_path, arcname=os.path.basename(thumb_path))

        # Metadata text file
        meta_content = f"""=======================================================
TUBEPULSE US - YOUTUBE AUTOMATION METADATA PACKAGE
Target Audience: United States Viewers
Niche: {seo_data.get('niche_name', 'General US')} (Avg US RPM: {seo_data.get('avg_us_rpm', '$30.00')})
Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
=======================================================

--- RECOMMENDED YOUTUBE TITLE ---
{seo_data.get('selected_title', '')}

--- ALTERNATIVE A/B TEST TITLES ---
"""
        for t in seo_data.get('titles', []):
            meta_content += f"[{t.get('ctr_score', 85)}% CTR Score] {t.get('title')}\n"

        meta_content += f"""
--- YOUTUBE DESCRIPTION & CHAPTERS ---
{seo_data.get('description', '')}

--- PINNED COMMENT ---
{seo_data.get('pinned_comment', '')}

--- TAGS (COPY & PASTE INTO YOUTUBE STUDIO) ---
{seo_data.get('tags_csv', '')}

--- HASHTAGS ---
{' '.join(seo_data.get('hashtags', []))}
"""
        z.writestr("METADATA_YOUTUBE.txt", meta_content)
        z.writestr("SCRIPT_VOICEOVER.txt", script_text)

    return f"/static/media/packages/{zip_filename}"

def simulate_youtube_api_upload(video_data: dict) -> dict:
    """
    Simulates a live direct upload to YouTube via YouTube Data API v3.
    Validates limits and returns a mock published YouTube response.
    """
    title = video_data.get("title", "")
    if len(title) > 100:
        return {"success": False, "error": "Title exceeds YouTube 100 character limit"}

    mock_id = f"us_{uuid.uuid4().hex[:10]}"
    return {
        "success": True,
        "video_id": mock_id,
        "watch_url": f"https://www.youtube.com/watch?v={mock_id}",
        "studio_url": f"https://studio.youtube.com/video/{mock_id}/edit",
        "published_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "privacy_status": "public",
        "category_id": "27", # Education / How-to
        "tags_count": len(video_data.get("tags", [])),
        "message": "Video successfully submitted to YouTube Data API pipeline!"
    }
