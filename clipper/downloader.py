"""Video + subtitle downloading via yt-dlp.

Supports YouTube, Twitch/Kick VODs, TikTok, Instagram, X, and hundreds of
other sites — anything yt-dlp can handle works as a clip source.
"""
from __future__ import annotations

import glob
import os

_VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".mov", ".m4v")


def _ydl(opts: dict):
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError(
            "yt-dlp is not installed. Run: pip install -r requirements.txt"
        ) from exc
    return yt_dlp.YoutubeDL(opts)


def download_video(url: str, out_dir: str = "clip_work", max_height: int = 1080) -> dict:
    """Download a video URL to out_dir. Returns info dict with local `path`."""
    os.makedirs(out_dir, exist_ok=True)
    outtmpl = os.path.join(os.path.abspath(out_dir), "%(id)s.%(ext)s")
    opts = {
        "format": f"bv*[height<={max_height}]+ba/b[height<={max_height}]/b",
        "merge_output_format": "mp4",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    with _ydl(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    vid = info.get("id", "video")
    cands = [
        p
        for p in glob.glob(os.path.join(out_dir, f"{vid}.*"))
        if p.lower().endswith(_VIDEO_EXTS)
    ]
    if not cands:
        raise RuntimeError(f"Download finished but no video file found for id={vid}")
    path = max(cands, key=os.path.getsize)
    return {
        "id": vid,
        "title": info.get("title", vid),
        "uploader": info.get("uploader") or info.get("channel") or "",
        "duration": float(info.get("duration") or 0),
        "url": info.get("webpage_url") or url,
        "path": os.path.abspath(path),
    }


def fetch_subtitles(url: str, out_dir: str = "clip_work", lang: str = "en") -> str | None:
    """Download manual or auto-generated subtitles only (no video).

    Returns the path of a .vtt file, or None when the video has no captions
    in the requested language. Free, fast, needs no API key.
    """
    os.makedirs(out_dir, exist_ok=True)
    outtmpl = os.path.join(os.path.abspath(out_dir), "subs_%(id)s.%(ext)s")
    opts = {
        "skip_download": True,
        "writeautomaticsub": True,
        "writesubtitles": True,
        "subtitleslangs": [f"{lang}.*", "en.*"] if lang != "en" else ["en.*"],
        "subtitlesformat": "vtt",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    try:
        with _ydl(opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception:
        return None

    vid = info.get("id", "")
    files = sorted(glob.glob(os.path.join(out_dir, f"subs_{vid}.*.vtt")))
    if not files:
        return None
    # Prefer an exact language match, e.g. subs_ID.en.vtt
    for p in files:
        if p.rsplit(".", 2)[-2].lower() == lang.lower():
            return os.path.abspath(p)
    return os.path.abspath(files[0])
