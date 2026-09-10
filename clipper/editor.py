"""Clip rendering with ffmpeg: cut -> 9:16 -> burn captions -> loudness normalize."""
from __future__ import annotations

import os
import re
import shutil
import subprocess

from .captions import build_ass
from .transcriber import Word

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Display font for captions. Downloaded once on first render if missing
# (deploy environments usually have network); falls back to bundled DejaVu.
FONT_URLS = {
    "Anton": ("Anton-Regular.ttf",
              "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"),
}

BUNDLED_FALLBACK = "DejaVu Sans"


def ensure_font(font: str) -> str:
    """Make sure `font` is usable; download it once or fall back to bundled."""
    if font in FONT_URLS:
        fname, url = FONT_URLS[font]
        target = os.path.join(ASSETS_DIR, fname)
        if os.path.exists(target):
            return font
        try:
            import urllib.request
            print(f"[editor] downloading {font} font...", flush=True)
            req = urllib.request.Request(url, headers={"User-Agent": "clipper/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) > 50_000:  # sanity check: real TTF, not an error page
                with open(target, "wb") as f:
                    f.write(data)
                return font
            print("[editor] font download looked wrong, using fallback", flush=True)
        except Exception as e:
            print(f"[editor] font download failed ({e}), using {BUNDLED_FALLBACK}",
                  flush=True)
        return BUNDLED_FALLBACK
    return font


def resolve_ffmpeg(explicit: str = "") -> str:
    if explicit and os.path.exists(explicit):
        return explicit
    env = os.environ.get("FFMPEG_BIN", "")
    if env and os.path.exists(env):
        return env
    which = shutil.which("ffmpeg")
    if which:
        return which
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    raise RuntimeError(
        "ffmpeg not found. Install it (nixpacks.toml already includes it on "
        "deploy) or `pip install imageio-ffmpeg`, or set FFMPEG_BIN."
    )


def probe(path: str, ffmpeg_bin: str = "") -> dict:
    ff = resolve_ffmpeg(ffmpeg_bin)
    proc = subprocess.run([ff, "-hide_banner", "-i", path],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    err = proc.stderr or ""
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", err)
    duration = 0.0
    if m:
        duration = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return {"duration": duration,
            "has_video": "Video:" in err,
            "has_audio": "Audio:" in err}


def _fesc(path: str) -> str:
    """Escape a path for use inside an ffmpeg filter argument."""
    return (path.replace("\\", "\\\\").replace(":", "\\:")
                .replace("'", "\\'").replace("[", "\\[").replace("]", "\\]")
                .replace(",", "\\,").replace(";", "\\;"))


def render_clip(src: str, start: float, end: float, words: list[Word],
                out_path: str, style: str = "crop", font: str = "Anton",
                fontsize: int = 92, highlight: str = "yellow",
                preset: str = "veryfast", crf: int = 21,
                ffmpeg_bin: str = "") -> str:
    """Render one vertical clip. Returns out_path."""
    ff = resolve_ffmpeg(ffmpeg_bin)
    if end <= start:
        raise ValueError(f"invalid range {start}-{end}")
    if style not in ("crop", "blur"):
        raise ValueError("style must be 'crop' or 'blur'")
    font = ensure_font(font)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    ass_path = os.path.abspath(out_path + ".ass")
    build_ass(words, start, end, ass_path, font=font,
              fontsize=fontsize, highlight=highlight)

    subs = (f"subtitles={_fesc(ass_path)}:fontsdir='{_fesc(ASSETS_DIR)}':"
            f"force_style='FontName={font},FontSize={fontsize},"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,"
            "BorderStyle=1,Outline=3,Shadow=2'")
    cover = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    if style == "crop":
        vf = f"{cover},{subs}"
    else:
        vf = (f"split[a][b];[a]{cover},gblur=sigma=45:steps=3[bg];"
              f"[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,{subs}")

    info = probe(src, ff)
    cmd = [ff, "-y", "-hide_banner", "-loglevel", "error",
           "-ss", f"{start:.2f}", "-i", src, "-t", f"{end - start:.2f}",
           "-vf", vf]
    if info["has_audio"]:
        cmd += ["-map", "0:v:0", "-map", "0:a:0?",
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2"]
    else:
        cmd += ["-map", "0:v:0", "-an"]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg render failed: {(proc.stderr or '')[-2500:]}")
    return out_path
