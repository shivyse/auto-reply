"""
TubePulse US - High-CTR YouTube Thumbnail Generator
Generates eye-catching, high-converting 1280x720 thumbnails optimized for American mobile & desktop feeds.
Uses Pillow to composite bold typography, contrast glows, urgency badges, and graphic cues.
"""

import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

THUMB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "media", "thumbnails")
os.makedirs(THUMB_DIR, exist_ok=True)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

THEMES = {
    "finance": {
        "bg_top": (10, 25, 47),
        "bg_bottom": (2, 10, 20),
        "accent": (16, 185, 129),     # Emerald green
        "badge_bg": (234, 179, 8),    # Gold
        "badge_text": (0, 0, 0),
        "text_highlight": (250, 204, 21), # Yellow
        "default_badge": "US WEALTH 2026"
    },
    "tech_ai": {
        "bg_top": (15, 23, 42),
        "bg_bottom": (30, 27, 75),
        "accent": (6, 182, 212),      # Cyan
        "badge_bg": (99, 102, 241),   # Indigo
        "badge_text": (255, 255, 255),
        "text_highlight": (56, 189, 248), # Sky blue
        "default_badge": "SILICON VALLEY LEAK"
    },
    "true_crime": {
        "bg_top": (24, 24, 27),
        "bg_bottom": (9, 9, 11),
        "accent": (239, 68, 68),      # Crimson red
        "badge_bg": (220, 38, 38),    # Red
        "badge_text": (255, 255, 255),
        "text_highlight": (248, 113, 113),
        "default_badge": "FBI UNSOLVED"
    },
    "luxury_megaprojects": {
        "bg_top": (30, 41, 59),
        "bg_bottom": (15, 23, 42),
        "accent": (245, 158, 11),     # Amber
        "badge_bg": (217, 119, 6),    # Dark amber
        "badge_text": (255, 255, 255),
        "text_highlight": (253, 224, 71),
        "default_badge": "$2 TRILLION SECRETS"
    },
    "viral_psychology": {
        "bg_top": (46, 16, 101),
        "bg_bottom": (15, 23, 42),
        "accent": (168, 85, 247),     # Purple
        "badge_bg": (236, 72, 153),   # Pink
        "badge_text": (255, 255, 255),
        "text_highlight": (244, 114, 182),
        "default_badge": "99% NEVER KNEW"
    },
    "us_real_estate": {
        "bg_top": (15, 23, 42),
        "bg_bottom": (8, 47, 73),
        "accent": (236, 72, 153),     # Rose
        "badge_bg": (244, 63, 94),    # Rose Red
        "badge_text": (255, 255, 255),
        "text_highlight": (251, 191, 36),
        "default_badge": "US HOUSING ALERT"
    }
}

def predict_ctr_score(title_text: str, badge_text: str, niche: str) -> dict:
    """Predicts CTR potential on YouTube US Home & Recommended feeds (0-10% scale)."""
    score = 6.2 # Baseline average YouTube US CTR
    words = (title_text + " " + badge_text).lower().split()

    # Power word bonuses
    if any(w in words for w in ["secret", "leak", "warning", "2026", "loophole", "irs", "fbi", "trillion"]):
        score += 1.4
    if any(w in words for w in ["stop", "never", "why", "shocking", "million", "cheaper"]):
        score += 1.1

    # Text length penalty if overly wordy (US feed users scan in 0.5s)
    if len(title_text.split()) > 7:
        score -= 0.6
    elif 3 <= len(title_text.split()) <= 6:
        score += 0.8

    predicted_ctr = min(11.8, round(score, 1))

    if predicted_ctr >= 8.5:
        tier = "Elite Viral Tier (Top 5% of US Feed)"
        tier_color = "#10b981"
    elif predicted_ctr >= 7.0:
        tier = "Above Average US Performance"
        tier_color = "#06b6d4"
    else:
        tier = "Moderate CTR (Consider punchier keywords)"
        tier_color = "#f59e0b"

    return {
        "predicted_ctr": f"{predicted_ctr}%",
        "tier": tier,
        "tier_color": tier_color,
        "recommendation": "Use 3-5 massive words. Ensure badge contrasts with the primary text."
    }

def generate_thumbnail(
    topic: str,
    niche: str = "finance",
    custom_badge: str = None,
    output_filename: str = None
) -> str:
    """
    Renders a 1280x720 high-CTR thumbnail for YouTube.
    """
    width, height = 1280, 720
    theme = THEMES.get(niche, THEMES["finance"])
    badge_text = custom_badge or theme["default_badge"]

    # Generate filename if not specified
    if not output_filename:
        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', topic[:25]).strip('_').lower()
        output_filename = f"thumb_{niche}_{clean_name}.png"

    output_path = os.path.join(THUMB_DIR, output_filename)

    # 1. Background Gradient
    img = Image.new("RGB", (width, height), theme["bg_bottom"])
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / float(height)
        r = int(theme["bg_top"][0] * (1 - ratio) + theme["bg_bottom"][0] * ratio)
        g = int(theme["bg_top"][1] * (1 - ratio) + theme["bg_bottom"][1] * ratio)
        b = int(theme["bg_top"][2] * (1 - ratio) + theme["bg_bottom"][2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 2. Add dynamic accent lighting glow circle on the right side
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    accent_rgba = (*theme["accent"], 45)
    glow_draw.ellipse([width - 450, -50, width + 250, height + 50], fill=accent_rgba)
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img.paste(glow, (0, 0), glow)
    draw = ImageDraw.Draw(img)

    # 3. Outer Contrast Border (Creates high visual separation against dark/light YouTube themes)
    border_width = 8
    draw.rectangle([0, 0, width - 1, height - 1], outline=theme["accent"], width=border_width)

    # Fonts
    try:
        font_badge = ImageFont.truetype(FONT_PATH, 32)
        font_headline = ImageFont.truetype(FONT_PATH, 68)
        font_sub = ImageFont.truetype(FONT_PATH, 44)
    except:
        font_badge = ImageFont.load_default()
        font_headline = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # 4. Draw Urgency Badge (e.g. "US TAX 2026", "TOP SECRET")
    badge_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    badge_w = badge_bbox[2] - badge_bbox[0]
    badge_h = badge_bbox[3] - badge_bbox[1]
    bx, by = 70, 70
    pad_x, pad_y = 24, 12

    # Badge Shadow & Box
    draw.rectangle([bx + 4, by + 4, bx + badge_w + pad_x * 2 + 4, by + badge_h + pad_y * 2 + 4], fill=(0, 0, 0, 180))
    draw.rounded_rectangle([bx, by, bx + badge_w + pad_x * 2, by + badge_h + pad_y * 2], radius=8, fill=theme["badge_bg"])
    draw.text((bx + pad_x, by + pad_y - 2), badge_text, fill=theme["badge_text"], font=font_badge)

    # 5. Format Headline text (split topic into 2-3 massive punchy lines)
    # Simplify words into high-impact uppercase punchlines
    words = topic.upper().split()
    if len(words) > 6:
        # Pick the most punchy phrase
        line1 = " ".join(words[:3])
        line2 = " ".join(words[3:6])
        line3 = " ".join(words[6:9]) if len(words) > 6 else ""
    elif len(words) > 3:
        line1 = " ".join(words[:2])
        line2 = " ".join(words[2:])
        line3 = ""
    else:
        line1 = " ".join(words)
        line2 = ""
        line3 = ""

    # Text positioning with heavy drop shadows for extreme contrast
    start_y = 190
    lines = [l for l in [line1, line2, line3] if l]

    for idx, line in enumerate(lines):
        curr_y = start_y + idx * 85
        # Alternating color: first line white, second line highlight yellow/cyan
        text_color = theme["text_highlight"] if idx == 1 else (255, 255, 255)

        # Thick drop shadow for maximum legibility on mobile
        for ox, oy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 5), (0, 8)]:
            draw.text((70 + ox, curr_y + oy), line, fill=(0, 0, 0), font=font_headline)
        draw.text((70, curr_y), line, fill=text_color, font=font_headline)

    # 6. Bottom Banner / Stat Callout
    banner_y = height - 120
    draw.rectangle([60, banner_y, width - 60, banner_y + 60], fill=(15, 23, 42, 220), outline=theme["accent"], width=2)
    stat_callout = f"★ US AUDIENCE EXCLUSIVE • 2026 ALGORITHM CERTIFIED • 1080p HD"
    draw.text((80, banner_y + 16), stat_callout, fill=(203, 213, 225), font=font_sub)

    # Save Thumbnail
    img.save(output_path, "PNG", quality=95)
    return output_path
