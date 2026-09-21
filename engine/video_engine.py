"""
TubePulse US - Kinetic Video Generator Engine
Renders high-retention YouTube Shorts (1080x1920) and Long-Form (1920x1080) MP4 videos.
Composites kinetic subtitle cards, animated bottom retention progress bars, pulsing audio visualizers,
and procedural background music using Pillow and FFmpeg.
"""

import os
import re
import math
import subprocess
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .audio_engine import synthesize_polyphonic_track, AUDIO_DIR

VIDEO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "media", "videos")
os.makedirs(VIDEO_DIR, exist_ok=True)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

THEME_COLORS = {
    "finance": {
        "primary": (16, 185, 129),    # Emerald
        "highlight": (250, 204, 21),  # Gold
        "bg_dark": (10, 15, 29),
        "badge": "US FINANCE REPORT"
    },
    "tech_ai": {
        "primary": (6, 182, 212),     # Cyan
        "highlight": (56, 189, 248),  # Sky blue
        "bg_dark": (15, 23, 42),
        "badge": "SILICON VALLEY INTEL"
    },
    "true_crime": {
        "primary": (239, 68, 68),     # Crimson
        "highlight": (252, 165, 165), # Light Red
        "bg_dark": (18, 18, 18),
        "badge": "UNSOLVED FBI ARCHIVE"
    },
    "luxury_megaprojects": {
        "primary": (245, 158, 11),    # Amber
        "highlight": (253, 224, 71),  # Bright Yellow
        "bg_dark": (15, 23, 42),
        "badge": "US MEGAPROJECT CLASSIFIED"
    },
    "viral_psychology": {
        "primary": (168, 85, 247),    # Purple
        "highlight": (244, 114, 182), # Pink
        "bg_dark": (20, 10, 35),
        "badge": "US VIRAL PSYCHOLOGY"
    },
    "us_real_estate": {
        "primary": (244, 63, 94),     # Rose
        "highlight": (251, 191, 36),  # Gold
        "bg_dark": (15, 23, 42),
        "badge": "US HOUSING DATA"
    }
}

def render_kinetic_card(
    width: int,
    height: int,
    headline: str,
    body_text: str,
    badge_label: str,
    niche: str,
    progress_pct: float,
    beat_step: int,
    output_path: str
):
    """Renders a single high-impact kinetic typography card frame."""
    theme = THEME_COLORS.get(niche, THEME_COLORS["finance"])
    img = Image.new("RGB", (width, height), theme["bg_dark"])
    draw = ImageDraw.Draw(img)

    # 1. Subtle Radial Ambient Glow
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    center_y = int(height * 0.45)
    g_draw.ellipse(
        [width//2 - 400, center_y - 400, width//2 + 400, center_y + 400],
        fill=(*theme["primary"], 35)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    img.paste(glow, (0, 0), glow)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font_badge = ImageFont.truetype(FONT_PATH, 28 if width < 1200 else 32)
        font_head = ImageFont.truetype(FONT_PATH, 54 if width < 1200 else 64)
        font_body = ImageFont.truetype(FONT_PATH, 38 if width < 1200 else 46)
        font_meta = ImageFont.truetype(FONT_PATH, 24 if width < 1200 else 28)
    except:
        font_badge = ImageFont.load_default()
        font_head = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_meta = ImageFont.load_default()

    # 2. Header Badge
    badge_y = 100 if height > 1500 else 60
    draw.rounded_rectangle([70, badge_y, 70 + 380, badge_y + 55], radius=10, fill=(*theme["primary"], 220))
    draw.text((85, badge_y + 12), f"● {badge_label}", fill=(255, 255, 255), font=font_badge)

    # 3. Sound Waveform Visualizer Simulation (Top right)
    wave_x = width - 260
    wave_y = badge_y + 10
    bar_heights = [18, 35, 22, 45, 30, 48, 26, 40, 20]
    for i, h in enumerate(bar_heights):
        bx = wave_x + i * 18
        draw.rectangle([bx, wave_y + (50 - h) // 2, bx + 10, wave_y + 50], fill=theme["highlight"])

    # 4. Kinetic Headline Box
    head_y = badge_y + 90
    words = headline.upper().split()
    line1 = " ".join(words[:4])
    line2 = " ".join(words[4:8]) if len(words) > 4 else ""

    draw.text((70, head_y), line1, fill=(255, 255, 255), font=font_head)
    if line2:
        draw.text((70, head_y + 70), line2, fill=theme["highlight"], font=font_head)

    # 5. Body Text Card with Viral Caption Highlighting
    card_top = head_y + (160 if line2 else 90)
    card_bottom = height - (240 if height > 1500 else 160)
    draw.rounded_rectangle([60, card_top, width - 60, card_bottom], radius=24, fill=(15, 23, 42, 230), outline=(51, 65, 85), width=3)

    # Wrap body text into lines
    body_words = body_text.split()
    body_lines = []
    curr = []
    for w in body_words:
        curr.append(w)
        if len(" ".join(curr)) > (26 if width < 1200 else 45):
            body_lines.append(" ".join(curr))
            curr = []
    if curr:
        body_lines.append(" ".join(curr))

    body_y = card_top + 60
    for idx, bl in enumerate(body_lines[:7]):
        # Highlight trigger words (e.g. $, numbers, critical keywords)
        text_fill = (255, 255, 255)
        if any(kw in bl.lower() for kw in ["$", "%", "tax", "secret", "fbi", "loophole", "million", "never", "trillion"]):
            text_fill = theme["highlight"]

        draw.text((100, body_y + idx * 60), bl, fill=text_fill, font=font_body)

    # 6. Bottom Retention Progress Bar (Proven to keep US mobile viewers hooked)
    bar_y = height - 20
    draw.rectangle([0, bar_y, width, height], fill=(30, 41, 59))
    prog_w = int(width * (progress_pct / 100.0))
    draw.rectangle([0, bar_y, prog_w, height], fill=theme["highlight"])

    # 7. Channel / Watermark Footer
    footer_y = card_bottom + 40
    draw.text((70, footer_y), "TubePulse US • Auto-Engineered for American Audiences", fill=(148, 163, 184), font=font_meta)

    img.save(output_path, "PNG")
    return output_path

def render_automated_video(
    script_data: dict,
    niche: str = "finance",
    format_type: str = "shorts",
    output_filename: str = None
) -> dict:
    """
    Renders a complete MP4 video from script data with audio synchronization and kinetic visuals.
    """
    is_shorts = (format_type.lower() == "shorts")
    width, height = (1080, 1920) if is_shorts else (1920, 1080)

    clean_topic = re.sub(r'[^a-zA-Z0-9]', '_', script_data.get("topic", "video")[:20]).strip('_').lower()
    if not output_filename:
        output_filename = f"vid_{'shorts' if is_shorts else 'long'}_{niche}_{clean_topic}.mp4"

    final_mp4_path = os.path.join(VIDEO_DIR, output_filename)

    # Temp workspace for frames
    temp_dir = os.path.join(VIDEO_DIR, f"temp_{clean_topic}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 1. Determine segments/beats to render
        beats = []
        if is_shorts:
            raw_beats = script_data.get("beats", [])
            if raw_beats:
                for b in raw_beats:
                    beats.append({
                        "label": b[1],
                        "text": b[2],
                        "duration": max(3, len(b[2].split()) // 3)
                    })
            else:
                beats = [
                    {"label": "HOOK ALERT", "text": script_data.get("hook", "Important Update for US Viewers"), "duration": 4},
                    {"label": "THE SHIFT", "text": script_data.get("full_text", "")[:120], "duration": 6},
                    {"label": "TAKE ACTION", "text": "Subscribe to stay ahead of the curve.", "duration": 4}
                ]
        else:
            sections = script_data.get("sections", [])
            for s in sections[:4]:
                beats.append({
                    "label": s.get("title", "KEY INSIGHT"),
                    "text": s.get("voiceover", "")[:140] + "...",
                    "duration": 5
                })

        total_duration = sum(b["duration"] for b in beats)
        theme = THEME_COLORS.get(niche, THEME_COLORS["finance"])

        # 2. Render each beat's frame image
        frame_files = []
        accumulated_dur = 0
        for i, b in enumerate(beats):
            progress_pct = min(98.0, round((accumulated_dur / float(total_duration)) * 100.0, 1))
            frame_path = os.path.join(temp_dir, f"slide_{i:02d}.png")
            render_kinetic_card(
                width=width,
                height=height,
                headline=b["label"],
                body_text=b["text"],
                badge_label=theme["badge"],
                niche=niche,
                progress_pct=progress_pct,
                beat_step=i + 1,
                output_path=frame_path
            )
            frame_files.append((frame_path, b["duration"]))
            accumulated_dur += b["duration"]

        # 3. Create FFmpeg concat demuxer file for smooth timed slides
        concat_txt = os.path.join(temp_dir, "input.txt")
        with open(concat_txt, "w") as f:
            for fpath, dur in frame_files:
                f.write(f"file '{os.path.abspath(fpath)}'\n")
                f.write(f"duration {dur}\n")
            # Repeat last file to satisfy concat demuxer spec
            if frame_files:
                f.write(f"file '{os.path.abspath(frame_files[-1][0])}'\n")

        # 4. Prepare Audio Bed
        bgm_type = "wall_street_pulse" if niche in ["finance", "tech_ai"] else ("true_crime_noir" if niche == "true_crime" else "viral_energetic")
        bgm_file = os.path.join(AUDIO_DIR, f"{bgm_type}_30s.wav")
        if not os.path.exists(bgm_file):
            bgm_file = synthesize_polyphonic_track(bgm_type, max(30.0, float(total_duration)))

        # 5. FFmpeg Encode: Concat slides + Loop audio + Render 1080p MP4
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_txt,
            "-stream_loop", "-1", "-i", bgm_file,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            "-r", "25",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(total_duration),
            "-movflags", "+faststart",
            "-shortest",
            final_mp4_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg render error: {result.stderr}")

        file_size_mb = round(os.path.getsize(final_mp4_path) / (1024 * 1024), 2)

        return {
            "status": "success",
            "video_path": final_mp4_path,
            "filename": output_filename,
            "url": f"/static/media/videos/{output_filename}",
            "duration": total_duration,
            "resolution": f"{width}x{height}",
            "format": "Shorts (9:16)" if is_shorts else "Long-Form (16:9)",
            "size_mb": file_size_mb,
            "niche": niche
        }

    finally:
        # Cleanup temp frames
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
