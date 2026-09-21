"""
TubePulse US - Viral Kinetic Video Rendering Engine
Transforms scripts into fast-paced, high-dopamine YouTube Shorts (1080x1920) and Long-Form (1920x1080) videos.
Replaces boring corporate presentation slides with rapid-fire 1-second cuts, giant Hormozi-style typography,
neon highlight pill boxes, camera viewfinder HUDs, pulsing audio visualizers, and cinematic sub-bass hits.
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

# High-voltage viral color themes
VIRAL_THEMES = {
    "warning": {
        "bg_dark": (10, 6, 12),
        "glow_color": (239, 68, 68),       # Crimson Red
        "badge_bg": (220, 38, 38),
        "badge_text": (255, 255, 255),
        "accent": (248, 113, 113),
        "pill_bg": (239, 68, 68),
        "pill_text": (255, 255, 255),
        "highlight_word": (254, 240, 138),  # Bright Yellow
        "default_sticker": "🚨 DO NOT IGNORE 🚨"
    },
    "money": {
        "bg_dark": (6, 16, 14),
        "glow_color": (16, 185, 129),      # Emerald Green
        "badge_bg": (234, 179, 8),         # Gold
        "badge_text": (0, 0, 0),
        "accent": (52, 211, 153),
        "pill_bg": (234, 179, 8),
        "pill_text": (0, 0, 0),
        "highlight_word": (250, 204, 21),  # Gold Yellow
        "default_sticker": "💰 $15,000 GLITCH 💰"
    },
    "mystery": {
        "bg_dark": (8, 14, 26),
        "glow_color": (6, 182, 212),       # Cyan Neon
        "badge_bg": (14, 165, 233),
        "badge_text": (255, 255, 255),
        "accent": (56, 189, 248),
        "pill_bg": (6, 182, 212),
        "pill_text": (0, 0, 0),
        "highlight_word": (103, 232, 249),
        "default_sticker": "🕵️ CLASSIFIED FBI 🕵️"
    },
    "shock": {
        "bg_dark": (18, 8, 28),
        "glow_color": (168, 85, 247),      # Electric Purple
        "badge_bg": (217, 70, 239),
        "badge_text": (255, 255, 255),
        "accent": (232, 121, 249),
        "pill_bg": (236, 72, 153),
        "pill_text": (255, 255, 255),
        "highlight_word": (253, 224, 71),
        "default_sticker": "⚡ SHOCKING TRUTH ⚡"
    }
}

def slice_script_into_rapid_beats(script_data: dict, format_type: str = "shorts"):
    """
    Splits any script into fast-paced 1.0 - 1.5s visual beats (2-4 words per beat).
    This creates relentless visual pacing identical to top viral YouTube Shorts.
    """
    is_shorts = (format_type.lower() == "shorts")
    raw_text = script_data.get("full_text", "")
    
    # Clean and split into individual sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', raw_text) if s.strip()]
    if not sentences:
        sentences = ["Stop scrolling and check your dollar bills right now.", "A massive glitch was discovered by collectors."]

    beats = []
    stickers = [
        "🚨 DO NOT IGNORE 🚨",
        "⚠️ SECRET LOOPHOLE ⚠️",
        "💵 $15,000 BOUNTY 💵",
        "🔍 LOOK CLOSELY 🔍",
        "🕵️ CLASSIFIED FILE 🕵️",
        "⚡ 99% NEVER KNEW ⚡",
        "👀 WATCH TILL END 👀",
        "🔥 VIRAL REVEAL 🔥"
    ]

    theme_keys = ["warning", "money", "mystery", "shock"]

    # Break each sentence into 2-4 word bursts
    beat_idx = 0
    for s_idx, sentence in enumerate(sentences):
        words = sentence.split()
        chunk_size = 3 if is_shorts else 4
        
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i + chunk_size]
            phrase = " ".join(chunk).upper()
            
            # Find emphasis word (numbers, dollar amounts, power words)
            emphasis = ""
            for w in chunk:
                clean_w = re.sub(r'[^a-zA-Z0-9$]', '', w).upper()
                if any(c in clean_w for c in ["$", "%", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]) or \
                   clean_w in ["SECRET", "NEVER", "STOP", "GLITCH", "BANNED", "FATAL", "VAULT", "DOOR", "STAR", "CASH", "TRUTH", "FBI", "TREASURY"]:
                    emphasis = clean_w
                    break

            theme = theme_keys[beat_idx % len(theme_keys)]
            sticker = stickers[beat_idx % len(stickers)]

            beats.append({
                "phrase": phrase,
                "emphasis": emphasis,
                "theme_key": theme,
                "sticker": sticker,
                "duration": 1.2 if is_shorts else 1.8
            })
            beat_idx += 1

    # Keep shorts between 14 to 22 beats (~18-28 seconds), long-form up to 30 beats for preview
    max_beats = 20 if is_shorts else 28
    return beats[:max_beats]

def render_viral_kinetic_frame(
    width: int,
    height: int,
    phrase: str,
    emphasis: str,
    sticker: str,
    theme_key: str,
    progress_pct: float,
    frame_idx: int,
    output_path: str
):
    """
    Renders a single high-voltage kinetic typography frame.
    No boring corporate cards! Full-screen energetic contrast with camera HUD, neon radial glow,
    giant center text with thick black outline, highlight pill boxes, and animated audio equalizer.
    """
    theme = VIRAL_THEMES.get(theme_key, VIRAL_THEMES["warning"])
    img = Image.new("RGB", (width, height), theme["bg_dark"])
    draw = ImageDraw.Draw(img)

    # 1. Energetic Radial Glow in center
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    center_y = int(height * 0.48)
    radius = 520
    g_draw.ellipse(
        [width//2 - radius, center_y - radius, width//2 + radius, center_y + radius],
        fill=(*theme["glow_color"], 55)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(130))
    img.paste(glow, (0, 0), glow)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font_huge = ImageFont.truetype(FONT_PATH, 105 if width < 1200 else 90)
        font_pill = ImageFont.truetype(FONT_PATH, 70 if width < 1200 else 60)
        font_badge = ImageFont.truetype(FONT_PATH, 34 if width < 1200 else 30)
        font_hud = ImageFont.truetype(FONT_PATH, 24 if width < 1200 else 22)
    except:
        font_huge = ImageFont.load_default()
        font_pill = ImageFont.load_default()
        font_badge = ImageFont.load_default()
        font_hud = ImageFont.load_default()

    # 2. Camera Viewfinder HUD Brackets (gives an authentic leaked/documentary feel)
    hud_color = (148, 163, 184, 180)
    bracket_len = 50
    margin = 50
    # Top-Left Bracket
    draw.line([(margin, margin), (margin + bracket_len, margin)], fill=hud_color, width=4)
    draw.line([(margin, margin), (margin, margin + bracket_len)], fill=hud_color, width=4)
    # Top-Right Bracket
    draw.line([(width - margin, margin), (width - margin - bracket_len, margin)], fill=hud_color, width=4)
    draw.line([(width - margin, margin), (width - margin, margin + bracket_len)], fill=hud_color, width=4)
    # Bottom-Left Bracket
    draw.line([(margin, height - margin), (margin + bracket_len, height - margin)], fill=hud_color, width=4)
    draw.line([(margin, height - margin), (margin, height - margin - bracket_len)], fill=hud_color, width=4)
    # Bottom-Right Bracket
    draw.line([(width - margin, height - margin), (width - margin - bracket_len, height - margin)], fill=hud_color, width=4)
    draw.line([(width - margin, height - margin), (width - margin, height - margin - bracket_len)], fill=hud_color, width=4)

    # Top HUD Status
    draw.text((margin + 10, margin + 8), "● REC [4K 60FPS]", fill=(239, 68, 68), font=font_hud)
    draw.text((width - margin - 220, margin + 8), f"US FEED #{frame_idx+1:02d}", fill=(203, 213, 225), font=font_hud)

    # 3. Top Urgency / Curiosity Sticker (High Contrast Pill)
    badge_y = 220 if height > 1500 else 90
    badge_bbox = draw.textbbox((0, 0), sticker, font=font_badge)
    bw = badge_bbox[2] - badge_bbox[0] + 48
    bh = badge_bbox[3] - badge_bbox[1] + 24
    bx = (width - bw) // 2

    # Drop shadow on badge
    draw.rounded_rectangle([bx + 4, badge_y + 4, bx + bw + 4, badge_y + bh + 4], radius=12, fill=(0, 0, 0, 160))
    draw.rounded_rectangle([bx, badge_y, bx + bw, badge_y + bh], radius=12, fill=theme["badge_bg"], outline=(255, 255, 255), width=2)
    draw.text((width // 2, badge_y + bh // 2), sticker, fill=theme["badge_text"], font=font_badge, anchor="mm")

    # 4. GIANT Center Kinetic Typography (Hormozi / Viral Pop Style)
    words = phrase.split()
    lines = []
    if len(words) <= 2:
        lines = [phrase]
    elif len(words) <= 4:
        lines = [" ".join(words[:2]), " ".join(words[2:])]
    else:
        lines = [" ".join(words[:2]), " ".join(words[2:4]), " ".join(words[4:])]

    text_center_y = int(height * 0.48)
    line_spacing = 115 if width < 1200 else 95
    start_y = text_center_y - (len(lines) * line_spacing) // 2

    for l_idx, line in enumerate(lines):
        curr_y = start_y + l_idx * line_spacing
        
        # Check if line contains emphasis word
        has_emphasis = emphasis and (emphasis in line.upper())
        text_color = theme["highlight_word"] if (l_idx == 1 or has_emphasis) else (255, 255, 255)

        # Draw thick black outline (stroke_width=8) so text pops off ANY background
        for ox, oy in [(-5, -5), (5, -5), (-5, 5), (5, 5), (0, 7), (0, 9)]:
            draw.text((width // 2 + ox, curr_y + oy), line, fill=(0, 0, 0), font=font_huge, anchor="mm")
        
        draw.text((width // 2, curr_y), line, fill=text_color, font=font_huge, anchor="mm")

    # 5. Highlight Pill Box (If an emphasis word exists, render a bright yellow pop card under the text)
    if emphasis:
        pill_y = start_y + len(lines) * line_spacing + 20
        pill_text = f"🔥 {emphasis} 🔥"
        p_bbox = draw.textbbox((0, 0), pill_text, font=font_pill)
        pw = p_bbox[2] - p_bbox[0] + 50
        ph = p_bbox[3] - p_bbox[1] + 28
        px = (width - pw) // 2
        
        # Pill shadow & box
        draw.rounded_rectangle([px + 5, pill_y + 5, px + pw + 5, pill_y + ph + 5], radius=16, fill=(0, 0, 0, 180))
        draw.rounded_rectangle([px, pill_y, px + pw, pill_y + ph], radius=16, fill=(250, 204, 21))
        draw.text((width // 2, pill_y + ph // 2 - 2), pill_text, fill=(0, 0, 0), font=font_pill, anchor="mm")

    # 6. Pulsing Audio Visualizer Waveform Bars (animated rhythm at bottom)
    wave_y = height - (260 if height > 1500 else 140)
    bar_count = 21
    bar_width = 14 if width < 1200 else 18
    gap = 8
    total_w = bar_count * (bar_width + gap)
    start_x = (width - total_w) // 2

    for b in range(bar_count):
        # Sine-based dynamic bar height simulating audio spectrum
        osc = math.sin((b * 0.45) + (frame_idx * 0.8)) * 0.5 + 0.5
        h_val = int(18 + osc * 65)
        bx = start_x + b * (bar_width + gap)
        draw.rounded_rectangle([bx, wave_y - h_val, bx + bar_width, wave_y + 10], radius=4, fill=theme["accent"])

    # 7. Animated Bottom Retention Progress Bar (Proven to keep viewers watching to 100%)
    prog_h = 16
    draw.rectangle([0, height - prog_h, width, height], fill=(15, 23, 42))
    fill_w = int(width * (progress_pct / 100.0))
    # Red & gold gradient progress fill
    draw.rectangle([0, height - prog_h, fill_w, height], fill=(239, 68, 68))
    if fill_w > 10:
        draw.rectangle([fill_w - 8, height - prog_h, fill_w, height], fill=(250, 204, 21))

    # 8. High-Energy Call To Action Prompt
    cta_y = wave_y + 60
    cta_text = "👇 TAP SUBSCRIBE TO UNLOCK PART 2" if is_shorts_aspect(width, height) else "🔥 TubePulse US • Daily High-RPM Curiosity Files"
    draw.text((width // 2, cta_y), cta_text, fill=(203, 213, 225), font=font_hud, anchor="mm")

    img.save(output_path, "PNG")
    return output_path

def is_shorts_aspect(w, h):
    return h > w

def render_automated_video(
    script_data: dict,
    niche: str = "finance",
    format_type: str = "shorts",
    output_filename: str = None
) -> dict:
    """
    Renders a viral kinetic video from script data with rapid-fire cuts and energetic audio.
    """
    is_shorts = (format_type.lower() == "shorts")
    width, height = (1080, 1920) if is_shorts else (1920, 1080)

    clean_topic = re.sub(r'[^a-zA-Z0-9]', '_', script_data.get("topic", "video")[:20]).strip('_').lower()
    if not output_filename:
        output_filename = f"vid_{'shorts' if is_shorts else 'long'}_{niche}_{clean_topic}.mp4"

    final_mp4_path = os.path.join(VIDEO_DIR, output_filename)

    # Temp workspace for frames
    temp_dir = os.path.join(VIDEO_DIR, f"temp_{clean_topic}_{int(math.floor(math.sin(1)*1000))}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 1. Break down script into rapid-fire 1-second viral beats
        beats = slice_script_into_rapid_beats(script_data, format_type)
        total_duration = sum(b["duration"] for b in beats)

        # 2. Render each rapid kinetic frame
        frame_files = []
        accumulated_dur = 0
        for idx, beat in enumerate(beats):
            progress_pct = min(99.0, round((accumulated_dur / float(total_duration)) * 100.0, 1))
            frame_path = os.path.join(temp_dir, f"frame_{idx:03d}.png")
            
            render_viral_kinetic_frame(
                width=width,
                height=height,
                phrase=beat["phrase"],
                emphasis=beat["emphasis"],
                sticker=beat["sticker"],
                theme_key=beat["theme_key"],
                progress_pct=progress_pct,
                frame_idx=idx,
                output_path=frame_path
            )
            frame_files.append((frame_path, beat["duration"]))
            accumulated_dur += beat["duration"]

        # 3. Create FFmpeg concat demuxer file for smooth timed slides
        concat_txt = os.path.join(temp_dir, "input.txt")
        with open(concat_txt, "w") as f:
            for fpath, dur in frame_files:
                f.write(f"file '{os.path.abspath(fpath)}'\n")
                f.write(f"duration {dur}\n")
            if frame_files:
                f.write(f"file '{os.path.abspath(frame_files[-1][0])}'\n")

        # 4. Prepare Audio Bed (High energy viral pulse with sub-bass)
        bgm_type = "viral_energetic" if is_shorts else ("wall_street_pulse" if niche in ["finance", "tech_ai"] else "true_crime_noir")
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
            "duration": round(total_duration, 1),
            "cuts_count": len(beats),
            "resolution": f"{width}x{height}",
            "format": "Shorts (9:16)" if is_shorts else "Long-Form (16:9)",
            "size_mb": file_size_mb,
            "niche": niche
        }

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
