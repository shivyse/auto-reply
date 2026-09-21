"""
TubePulse US - High-Octane Viral Video Rendering Engine
Implements the 2026 YouTube Shorts Retention Playbook:
- First-frame instant hook (0.0s, no intro cards, no logo delays)
- Rapid-fire visual changes every 1.1 - 1.4 seconds
- Procedural dynamic B-Roll canvas (rising profit charts, classified radar HUD, cyber grid, danger rings)
- Giant Hormozi-style kinetic typography with 10px black stroke outline in the middle third safe zone
- Exploding neon yellow / crimson highlight pill boxes on power words
- Camera Viewfinder HUD brackets (REC ● 4K 60FPS)
- Synchronized multi-layer sound design (808 sub boom, cut whooshes, chime payoff)
- Seamless infinite-watch replay loop
"""

import os
import re
import math
import subprocess
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .audio_engine import generate_viral_soundtrack_with_sfx, AUDIO_DIR

VIDEO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "media", "videos")
os.makedirs(VIDEO_DIR, exist_ok=True)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# High-voltage viral color schemes
VIRAL_THEMES = {
    "warning": {
        "bg_dark": (12, 6, 10),
        "glow_color": (239, 68, 68),       # Crimson Red
        "badge_bg": (220, 38, 38),
        "badge_text": (255, 255, 255),
        "accent": (248, 113, 113),
        "highlight_word": (254, 240, 138),  # Bright Yellow
        "default_sticker": "🚨 DO NOT IGNORE 🚨"
    },
    "money": {
        "bg_dark": (6, 16, 12),
        "glow_color": (16, 185, 129),      # Emerald Green
        "badge_bg": (234, 179, 8),         # Gold
        "badge_text": (0, 0, 0),
        "accent": (52, 211, 153),
        "highlight_word": (250, 204, 21),  # Gold Yellow
        "default_sticker": "💰 $15,000 GLITCH 💰"
    },
    "mystery": {
        "bg_dark": (8, 14, 26),
        "glow_color": (6, 182, 212),       # Cyan Neon
        "badge_bg": (14, 165, 233),
        "badge_text": (255, 255, 255),
        "accent": (56, 189, 248),
        "highlight_word": (103, 232, 249),
        "default_sticker": "🕵️ CLASSIFIED FBI 🕵️"
    },
    "shock": {
        "bg_dark": (18, 8, 28),
        "glow_color": (168, 85, 247),      # Electric Purple
        "badge_bg": (217, 70, 239),
        "badge_text": (255, 255, 255),
        "accent": (232, 121, 249),
        "highlight_word": (253, 224, 71),
        "default_sticker": "⚡ SHOCKING TRUTH ⚡"
    }
}

def slice_script_into_rapid_beats(script_data: dict, format_type: str = "shorts"):
    """
    Splits any script into fast-paced 1.1 - 1.4s visual beats (2-4 words per beat).
    This creates relentless visual pacing identical to top viral YouTube Shorts.
    """
    is_shorts = (format_type.lower() == "shorts")
    raw_text = script_data.get("full_text", "")
    
    sentences = [s.strip() for s in re.split(r'[.!?]+', raw_text) if s.strip()]
    if not sentences:
        sentences = [
            "Stop scrolling and check your dollar bills right now.",
            "A massive printing error was uncovered by collectors.",
            "If your serial number has a tiny star symbol next to it.",
            "It could be worth fifteen thousand dollars cash.",
            "Check your wallet before you spend it today."
        ]

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
    beat_idx = 0

    for sentence in sentences:
        words = sentence.split()
        chunk_size = 3 if is_shorts else 4
        
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i + chunk_size]
            phrase = " ".join(chunk).upper()
            
            # Find emphasis word
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
                "duration": 1.2 if is_shorts else 1.6
            })
            beat_idx += 1

    max_beats = 20 if is_shorts else 28
    return beats[:max_beats]

def draw_procedural_broll(draw, width, height, niche, frame_idx, theme):
    """
    Draws dynamic, animated procedural B-roll in the top half of the screen
    so the viewer is constantly stimulated by motion graphics.
    """
    top_y = 120 if height > 1500 else 60
    bottom_y = 660 if height > 1500 else 420

    if niche in ["finance", "us_real_estate"]:
        # Animated Stock/Profit Chart with Grid
        for gy in range(top_y + 40, bottom_y, 70):
            draw.line([(80, gy), (width - 80, gy)], fill=(16, 45, 30), width=2)
        for gx in range(80, width - 80, 110):
            draw.line([(gx, top_y + 40), (gx, bottom_y)], fill=(16, 45, 30), width=2)

        # Dynamic rising trendline oscillating with frame_idx
        pts = []
        step_x = (width - 240) // 5
        for i in range(6):
            px = 120 + i * step_x
            py = bottom_y - 40 - int(i * 65 + math.sin(i + frame_idx * 0.7) * 25)
            pts.append((px, max(top_y + 50, py)))

        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=(16, 185, 129), width=8)
            draw.ellipse([pts[i][0]-8, pts[i][1]-8, pts[i][0]+8, pts[i][1]+8], fill=(250, 204, 21))

        # Target peak marker
        last_pt = pts[-1]
        draw.ellipse([last_pt[0]-14, last_pt[1]-14, last_pt[0]+14, last_pt[1]+14], fill=(255, 255, 255), outline=(16, 185, 129), width=4)

    elif niche in ["true_crime", "luxury_megaprojects"]:
        # FBI Laser Crosshair Radar & Target Zone
        cx, cy = width // 2, (top_y + bottom_y) // 2
        for r in [90, 180, 260]:
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(239, 68, 68), width=3)
        # Laser crosshairs
        draw.line([(cx - 300, cy), (cx + 300, cy)], fill=(239, 68, 68), width=3)
        draw.line([(cx, cy - 240), (cx, cy + 240)], fill=(239, 68, 68), width=3)
        # Blinking radar sweep line
        ang = (frame_idx * 0.6)
        rx = cx + int(240 * math.cos(ang))
        ry = cy + int(240 * math.sin(ang))
        draw.line([(cx, cy), (rx, ry)], fill=(255, 255, 255), width=4)

    else:
        # Cyber / Psychology Grid Perspective
        cx, cy = width // 2, bottom_y - 20
        for i in range(-5, 6):
            draw.line([(cx + i * 40, top_y + 60), (cx + i * 140, bottom_y + 60)], fill=theme["accent"], width=2)
        for gy in range(top_y + 60, bottom_y + 60, 45):
            ratio = (gy - top_y) / float(bottom_y - top_y)
            draw.line([(cx - int(450 * ratio), gy), (cx + int(450 * ratio), gy)], fill=theme["accent"], width=2)

def render_viral_kinetic_frame(
    width: int,
    height: int,
    phrase: str,
    emphasis: str,
    sticker: str,
    theme_key: str,
    progress_pct: float,
    frame_idx: int,
    niche: str,
    output_path: str
):
    """
    Renders a single high-voltage kinetic typography frame.
    Layers: Camera HUD + Procedural B-Roll + Giant Center Typography + Audio Visualizer + Progress Line.
    """
    theme = VIRAL_THEMES.get(theme_key, VIRAL_THEMES["warning"])
    img = Image.new("RGB", (width, height), theme["bg_dark"])
    draw = ImageDraw.Draw(img)

    # 1. Radial Lighting Glow
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    center_y = int(height * 0.52)
    radius = 540
    g_draw.ellipse(
        [width//2 - radius, center_y - radius, width//2 + radius, center_y + radius],
        fill=(*theme["glow_color"], 65)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img.paste(glow, (0, 0), glow)
    draw = ImageDraw.Draw(img)

    # 2. Procedural B-Roll Visual Canvas in top half
    draw_procedural_broll(draw, width, height, niche, frame_idx, theme)

    # Fonts
    try:
        font_huge = ImageFont.truetype(FONT_PATH, 108 if width < 1200 else 92)
        font_pill = ImageFont.truetype(FONT_PATH, 72 if width < 1200 else 62)
        font_badge = ImageFont.truetype(FONT_PATH, 36 if width < 1200 else 32)
        font_hud = ImageFont.truetype(FONT_PATH, 24 if width < 1200 else 22)
    except:
        font_huge = ImageFont.load_default()
        font_pill = ImageFont.load_default()
        font_badge = ImageFont.load_default()
        font_hud = ImageFont.load_default()

    # 3. Camera Viewfinder HUD Brackets (Top & Bottom corners)
    hud_color = (148, 163, 184, 190)
    bracket_len = 50
    margin = 50
    draw.line([(margin, margin), (margin + bracket_len, margin)], fill=hud_color, width=4)
    draw.line([(margin, margin), (margin, margin + bracket_len)], fill=hud_color, width=4)
    draw.line([(width - margin, margin), (width - margin - bracket_len, margin)], fill=hud_color, width=4)
    draw.line([(width - margin, margin), (width - margin, margin + bracket_len)], fill=hud_color, width=4)

    # Top Status Text
    draw.text((margin + 12, margin + 10), "● REC [4K 60FPS]", fill=(239, 68, 68), font=font_hud)
    draw.text((width - margin - 230, margin + 10), f"US FEED #{frame_idx+1:02d}", fill=(203, 213, 225), font=font_hud)

    # 4. Top Urgency / Curiosity Sticker (High-Contrast Pill with Drop Shadow)
    badge_y = 690 if height > 1500 else 440
    badge_bbox = draw.textbbox((0, 0), sticker, font=font_badge)
    bw = badge_bbox[2] - badge_bbox[0] + 52
    bh = badge_bbox[3] - badge_bbox[1] + 26
    bx = (width - bw) // 2

    draw.rounded_rectangle([bx + 4, badge_y + 4, bx + bw + 4, badge_y + bh + 4], radius=14, fill=(0, 0, 0, 210))
    draw.rounded_rectangle([bx, badge_y, bx + bw, badge_y + bh], radius=14, fill=theme["badge_bg"], outline=(255, 255, 255), width=2)
    draw.text((width // 2, badge_y + bh // 2 - 2), sticker, fill=theme["badge_text"], font=font_badge, anchor="mm")

    # 5. GIANT Center Kinetic Typography (Hormozi / MrBeast Style)
    words = phrase.split()
    lines = []
    if len(words) <= 2:
        lines = [phrase]
    elif len(words) <= 4:
        lines = [" ".join(words[:2]), " ".join(words[2:])]
    else:
        lines = [" ".join(words[:2]), " ".join(words[2:4]), " ".join(words[4:])]

    text_center_y = int(height * 0.60)
    line_spacing = 118 if width < 1200 else 98
    start_y = text_center_y - (len(lines) * line_spacing) // 2

    for l_idx, line in enumerate(lines):
        curr_y = start_y + l_idx * line_spacing
        has_emphasis = emphasis and (emphasis in line.upper())
        text_color = theme["highlight_word"] if (l_idx == 1 or has_emphasis) else (255, 255, 255)

        # Thick 10px black outline for 100% legibility on any mobile screen
        for ox, oy in [(-6, -6), (6, -6), (-6, 6), (6, 6), (0, 8), (0, 10)]:
            draw.text((width // 2 + ox, curr_y + oy), line, fill=(0, 0, 0), font=font_huge, anchor="mm")
        
        draw.text((width // 2, curr_y), line, fill=text_color, font=font_huge, anchor="mm")

    # 6. Highlight Pill Box for Key Power Word
    if emphasis:
        pill_y = start_y + len(lines) * line_spacing + 24
        pill_text = f"🔥 {emphasis} 🔥"
        p_bbox = draw.textbbox((0, 0), pill_text, font=font_pill)
        pw = p_bbox[2] - p_bbox[0] + 54
        ph = p_bbox[3] - p_bbox[1] + 28
        px = (width - pw) // 2
        
        draw.rounded_rectangle([px + 5, pill_y + 5, px + pw + 5, pill_y + ph + 5], radius=16, fill=(0, 0, 0, 200))
        draw.rounded_rectangle([px, pill_y, px + pw, pill_y + ph], radius=16, fill=(250, 204, 21), outline=(255, 255, 255), width=2)
        draw.text((width // 2, pill_y + ph // 2 - 2), pill_text, fill=(0, 0, 0), font=font_pill, anchor="mm")

    # 7. Pulsing Audio Visualizer Waveform Bars (Bottom Equalizer)
    wave_y = height - (240 if height > 1500 else 130)
    bar_count = 23
    bar_width = 14 if width < 1200 else 18
    gap = 8
    total_w = bar_count * (bar_width + gap)
    start_x = (width - total_w) // 2

    for b in range(bar_count):
        osc = math.sin((b * 0.42) + (frame_idx * 0.9)) * 0.5 + 0.5
        h_val = int(16 + osc * 70)
        bx = start_x + b * (bar_width + gap)
        draw.rounded_rectangle([bx, wave_y - h_val, bx + bar_width, wave_y + 10], radius=4, fill=theme["accent"])

    # 8. Animated Bottom Retention Progress Bar
    prog_h = 16
    draw.rectangle([0, height - prog_h, width, height], fill=(15, 23, 42))
    fill_w = int(width * (progress_pct / 100.0))
    draw.rectangle([0, height - prog_h, fill_w, height], fill=(239, 68, 68))
    if fill_w > 12:
        draw.rectangle([fill_w - 10, height - prog_h, fill_w, height], fill=(250, 204, 21))

    # 9. Bottom Call To Action Hook
    cta_y = wave_y + 65
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
    Renders a viral kinetic video from script data with rapid-fire cuts and sound design.
    """
    is_shorts = (format_type.lower() == "shorts")
    width, height = (1080, 1920) if is_shorts else (1920, 1080)

    clean_topic = re.sub(r'[^a-zA-Z0-9]', '_', script_data.get("topic", "video")[:20]).strip('_').lower()
    if not output_filename:
        output_filename = f"vid_{'shorts' if is_shorts else 'long'}_{niche}_{clean_topic}.mp4"

    final_mp4_path = os.path.join(VIDEO_DIR, output_filename)

    temp_dir = os.path.join(VIDEO_DIR, f"temp_{clean_topic}_{int(math.floor(math.sin(1)*1000))}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 1. Break down script into rapid-fire 1-second viral beats
        beats = slice_script_into_rapid_beats(script_data, format_type)
        total_duration = sum(b["duration"] for b in beats)

        # 2. Render each rapid kinetic frame with B-roll & HUD
        frame_files = []
        cut_timestamps = []
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
                niche=niche,
                output_path=frame_path
            )
            frame_files.append((frame_path, beat["duration"]))
            accumulated_dur += beat["duration"]
            cut_timestamps.append(round(accumulated_dur, 2))

        # 3. Create FFmpeg concat demuxer file
        concat_txt = os.path.join(temp_dir, "input.txt")
        with open(concat_txt, "w") as f:
            for fpath, dur in frame_files:
                f.write(f"file '{os.path.abspath(fpath)}'\n")
                f.write(f"duration {dur}\n")
            if frame_files:
                f.write(f"file '{os.path.abspath(frame_files[-1][0])}'\n")

        # 4. Generate Adrenaline-Pumping Sound Design Track with 808 Sub Boom & Cut Whooshes!
        bgm_file = os.path.join(temp_dir, "soundtrack.wav")
        generate_viral_soundtrack_with_sfx(total_duration, niche, cut_timestamps[:-1], bgm_file)

        # 5. FFmpeg Encode: Concat slides + Sound-Designed Audio + 1080p MP4
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_txt,
            "-i", bgm_file,
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
