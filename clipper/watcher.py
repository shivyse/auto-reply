"""Fully-automatic mode: watch YouTube channels, clip every new upload.

Uses the public channel RSS feeds — no YouTube API key needed.

Channel identifiers accepted:
  - channel id:            UCxxxxxxxxxxxxxxxxxxxxxx
  - channel URL:           https://www.youtube.com/channel/UC...
  - handle / custom URL:   https://www.youtube.com/@SomeCreator  (resolved via yt-dlp)
"""
from __future__ import annotations

import asyncio
import inspect
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

_ATOM = "{http://www.w3.org/2005/Atom}"


@dataclass
class WatchedVideo:
    id: str
    title: str
    url: str
    published: str
    channel: str = ""


def resolve_channel_id(channel: str) -> str:
    channel = channel.strip()
    m = re.search(r"(UC[\w-]{22})", channel)
    if m:
        return m.group(1)
    url = channel if channel.startswith("http") else f"https://www.youtube.com/{channel.lstrip('/')}"
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("yt-dlp is required to resolve @" + channel) from exc
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True,
                           "extract_flat": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    cid = (info or {}).get("channel_id") or ""
    if not cid:
        # flat channel extraction sometimes nests under entries
        for e in (info or {}).get("entries", []) or []:
            if isinstance(e, dict) and e.get("channel_id"):
                cid = e["channel_id"]
                break
    if not cid:
        raise RuntimeError(f"Could not resolve channel id for: {channel}")
    return cid


def fetch_channel_videos(channel_id: str, limit: int = 5,
                         timeout: int = 30) -> list[WatchedVideo]:
    feed = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(feed, headers={"User-Agent": "clipper/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        xml = r.read()
    root = ET.fromstring(xml)
    vids: list[WatchedVideo] = []
    for entry in root.findall(f"{_ATOM}entry")[:limit]:
        def txt(tag: str) -> str:
            el = entry.find(f"{_ATOM}{tag}")
            return (el.text or "").strip() if el is not None else ""
        vid = txt("id").replace("yt:video:", "")
        link = entry.find(f"{_ATOM}link")
        href = link.get("href", "") if link is not None else ""
        if vid:
            vids.append(WatchedVideo(id=vid, title=txt("title") or vid,
                                     url=href or f"https://youtu.be/{vid}",
                                     published=txt("published")))
    return vids


def load_state(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1)


def poll_once(channels: list[str], state_path: str,
              limit: int = 3) -> list[tuple[str, WatchedVideo]]:
    """Check channels for new videos. Returns [(channel, video), ...] oldest-first."""
    state = load_state(state_path)
    fresh: list[tuple[str, WatchedVideo]] = []
    for ch in channels:
        try:
            cid = resolve_channel_id(ch)
            videos = fetch_channel_videos(cid, limit=limit)
        except Exception as e:
            print(f"[watcher] {ch}: check failed ({e})", flush=True)
            continue
        seen = set(state.get(cid, {}).get("seen", []))
        new = [v for v in videos if v.id not in seen]
        if not seen:
            # first run: mark latest as seen, don't clip the backlog
            print(f"[watcher] {ch}: tracking {len(videos)} video(s), "
                  "will clip future uploads", flush=True)
        else:
            for v in reversed(new):  # oldest first
                print(f"[watcher] {ch}: NEW {v.title} ({v.url})", flush=True)
                fresh.append((ch, v))
        state[cid] = {"channel": ch,
                      "seen": ([v.id for v in videos] + sorted(seen))[:50]}
    save_state(state, state_path)
    return fresh


async def watch_loop(channels: list[str], state_path: str, interval_min: float,
                     callback) -> None:
    """Poll forever, calling `callback(channel, video)` (sync or async) on news."""
    print(f"[watcher] watching {len(channels)} channel(s) every {interval_min} min",
          flush=True)
    while True:
        try:
            for ch, video in await asyncio.to_thread(poll_once, channels, state_path):
                try:
                    res = callback(ch, video)
                    if inspect.isawaitable(res):
                        await res
                except Exception as e:
                    print(f"[watcher] callback failed for {video.url}: {e}", flush=True)
        except Exception as e:
            print(f"[watcher] poll error: {e}", flush=True)
        await asyncio.sleep(max(60.0, interval_min * 60))
