"""End-to-end clipping pipeline.

    python -m clipper.pipeline --url <video-url> --shorts 3
    python -m clipper.pipeline --file video.mp4 --transcript t.json --no-llm

Steps: source -> transcript -> viral moments -> vertical captioned mp4s.
"""
from __future__ import annotations

import argparse
import json
import os

from .config import ClipperConfig
from .downloader import download_video, fetch_subtitles
from .editor import probe, render_clip
from .moments import Moment, pick_moments
from .transcriber import (Segment, load_transcript, save_transcript,
                          transcribe_api, transcribe_local, vtt_to_segments,
                          words_in_range)


def _get_transcript(url: str | None, media_path: str, source_id: str,
                    cfg: ClipperConfig, transcript_path: str | None = None):
    if transcript_path:
        print(f"[pipeline] loading transcript {transcript_path}", flush=True)
        return load_transcript(transcript_path), "provided"

    mode = cfg.transcribe_mode
    if mode in ("auto", "subs") and url:
        print("[pipeline] trying video subtitles (free)...", flush=True)
        vtt = fetch_subtitles(url, cfg.work_dir, cfg.subs_lang)
        if vtt:
            segs = vtt_to_segments(vtt)
            if segs:
                print(f"[pipeline] got {len(segs)} subtitle cues", flush=True)
                return segs, "subs"
        if mode == "subs":
            raise RuntimeError("No subtitles found for this video. Use --transcribe local or api.")

    if cfg.openai_api_key and mode in ("auto", "api"):
        print("[pipeline] transcribing via API...", flush=True)
        return transcribe_api(media_path, cfg.openai_api_key, cfg.openai_base_url), "api"

    if mode in ("auto", "local"):
        print(f"[pipeline] transcribing locally (whisper {cfg.whisper_model})...",
              flush=True)
        return transcribe_local(
            media_path, cfg.whisper_model, cfg.whisper_device, cfg.whisper_compute), "local"

    raise RuntimeError("No transcription method available. Set OPENAI_API_KEY, "
                       "install faster-whisper, or use subtitles.")


def run_job(url: str | None = None,
            file_path: str | None = None,
            transcript_path: str | None = None,
            cfg: ClipperConfig | None = None,
            count: int | None = None,
            title_prefix: str = "") -> dict:
    """Run the full pipeline. Returns result dict with clip file paths + meta."""
    cfg = cfg or ClipperConfig.from_env()
    count = count or cfg.clip_count
    os.makedirs(cfg.work_dir, exist_ok=True)
    os.makedirs(cfg.output_dir, exist_ok=True)

    # 1. source
    if file_path:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"video not found: {file_path}")
        media_path = os.path.abspath(file_path)
        source_id = os.path.splitext(os.path.basename(file_path))[0][:40]
        duration = probe(media_path, cfg.ffmpeg_bin)["duration"]
        source = {"id": source_id, "title": source_id, "uploader": "",
                  "duration": duration, "url": "", "path": media_path}
        print(f"[pipeline] source file: {media_path} ({duration:.1f}s)", flush=True)
    elif url:
        print(f"[pipeline] downloading {url} ...", flush=True)
        source = download_video(url, cfg.work_dir)
        media_path = source["path"]
        source_id = source["id"]
        if not source["duration"]:
            source["duration"] = probe(media_path, cfg.ffmpeg_bin)["duration"]
        print(f"[pipeline] downloaded: {source['title']} ({source['duration']:.1f}s)",
              flush=True)
    else:
        raise ValueError("provide url or file_path")

    # 2. transcript
    segments: list[Segment] = []
    segments, via = _get_transcript(url, media_path, source_id, cfg, transcript_path)
    tpath = os.path.join(cfg.work_dir, f"{source_id}.transcript.json")
    save_transcript(segments, tpath)

    # 3. moments
    moments: list[Moment] = pick_moments(
        segments, source["duration"], count, cfg.min_len, cfg.max_len,
        use_llm=cfg.use_llm, api_key=cfg.openai_api_key,
        base_url=cfg.openai_base_url, model=cfg.openai_model)

    # 4. render
    clips = []
    for i, m in enumerate(moments, 1):
        out = os.path.join(cfg.output_dir, f"{source_id}_clip{i:02d}.mp4")
        title = f"{title_prefix}{m.title}" if title_prefix else m.title
        print(f"[pipeline] rendering clip {i}/{len(moments)} "
              f"[{m.start:.1f}-{m.end:.1f}s] {title}", flush=True)
        words = words_in_range(segments, m.start, m.end)
        render_clip(media_path, m.start, m.end, words, out, style=cfg.style,
                    font=cfg.caption_font, fontsize=cfg.caption_fontsize,
                    highlight=cfg.highlight, ffmpeg_bin=cfg.ffmpeg_bin)
        clips.append({"path": os.path.abspath(out), "title": title or f"Clip {i}",
                      "hook": m.hook, "hashtags": m.hashtags,
                      "start": m.start, "end": m.end, "score": m.score,
                      "reason": m.reason})

    meta_path = os.path.join(cfg.output_dir, f"{source_id}_clips.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"source": source, "transcript_via": via,
                   "transcript": tpath, "clips": clips},
                  f, ensure_ascii=False, indent=1)
    print(f"[pipeline] done: {len(clips)} clip(s) -> {cfg.output_dir}", flush=True)
    return {"source": source, "transcript": tpath, "via": via,
            "clips": clips, "meta": meta_path}


def main() -> None:
    ap = argparse.ArgumentParser(description="Auto-clip videos into vertical shorts")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="video URL (YouTube, Twitch VOD, TikTok, ...)")
    src.add_argument("--file", help="local video file")
    ap.add_argument("--transcript", help="pre-made transcript JSON (skip transcribe)")
    ap.add_argument("--shorts", "-n", type=int, default=None)
    ap.add_argument("--min-len", type=float, default=None)
    ap.add_argument("--max-len", type=float, default=None)
    ap.add_argument("--style", choices=["crop", "blur"], default=None)
    ap.add_argument("--transcribe", choices=["auto", "subs", "local", "api"], default=None)
    ap.add_argument("--no-llm", action="store_true", help="use heuristic scoring only")
    ap.add_argument("--out", default=None)
    ap.add_argument("--title-prefix", default="")
    args = ap.parse_args()

    cfg = ClipperConfig.from_env()
    if args.shorts: cfg.clip_count = args.shorts
    if args.min_len: cfg.min_len = args.min_len
    if args.max_len: cfg.max_len = args.max_len
    if args.style: cfg.style = args.style
    if args.transcribe: cfg.transcribe_mode = args.transcribe
    if args.no_llm: cfg.use_llm = False
    if args.out: cfg.output_dir = args.out

    result = run_job(url=args.url, file_path=args.file,
                     transcript_path=args.transcript, cfg=cfg,
                     title_prefix=args.title_prefix)
    print(json.dumps({k: v for k, v in result.items() if k != "source"},
                     indent=1, default=str))


if __name__ == "__main__":
    main()
