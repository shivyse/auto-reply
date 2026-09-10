"""Speech-to-text with word-level timestamps.

Three engines (first available wins in 'auto' mode):
1. Video subtitles via yt-dlp (free, instant)     -> transcriber.vtt_to_segments
2. Local Whisper (free, offline, needs faster-whisper or openai-whisper)
3. OpenAI-compatible transcription API (needs OPENAI_API_KEY, light deploy)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import urllib.request
from dataclasses import asdict, dataclass


@dataclass
class Word:
    start: float
    end: float
    text: str


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[Word]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def save_transcript(segments: list[Segment], path: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in segments], f, ensure_ascii=False, indent=1)
    return path


def load_transcript(path: str) -> list[Segment]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out = []
    for s in raw:
        out.append(
            Segment(
                float(s["start"]),
                float(s["end"]),
                s.get("text", ""),
                [Word(float(w["start"]), float(w["end"]), w.get("text", "")) for w in s.get("words", [])],
            )
        )
    return out


def words_in_range(segments: list[Segment], start: float, end: float) -> list[Word]:
    words: list[Word] = []
    for s in segments:
        if s.end < start or s.start > end:
            continue
        for w in s.words:
            if w.end >= start and w.start <= end and w.text.strip():
                words.append(w)
    words.sort(key=lambda w: w.start)
    return words


def prompt_text(segments: list[Segment]) -> str:
    """Timestamped transcript formatted for the LLM moment-picker."""
    lines = []
    for s in segments:
        if s.text.strip():
            lines.append(f"[{_ts(s.start)} -> {_ts(s.end)}] {s.text.strip()}")
    return "\n".join(lines)


def _ts(sec: float) -> str:
    m, s = divmod(max(0.0, sec), 60)
    return f"{int(m):02d}:{s:05.2f}"


# --------------------------------------------------------------------------- #
# engine 1: local whisper
# --------------------------------------------------------------------------- #
def transcribe_local(
    media_path: str,
    model_size: str = "small",
    device: str = "cpu",
    compute_type: str = "int8",
    language: str | None = None,
    beam_size: int = 5,
) -> list[Segment]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        WhisperModel = None
    if WhisperModel is not None:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        gen, _info = model.transcribe(
            media_path, beam_size=beam_size, language=language,
            word_timestamps=True, vad_filter=True,
        )
        out: list[Segment] = []
        for s in gen:
            words = [
                Word(float(w.start), float(w.end), w.word.strip())
                for w in (s.words or []) if w.word.strip()
            ]
            out.append(Segment(float(s.start), float(s.end), s.text.strip(), words))
        return out

    try:
        import whisper  # openai-whisper fallback
    except ImportError:
        raise RuntimeError(
            "No local Whisper installed. Options:\n"
            "  - pip install faster-whisper   (free, offline, recommended)\n"
            "  - set OPENAI_API_KEY           (lightweight API transcription)\n"
            "  - use --transcribe subs        (YouTube captions, free)"
        )
    model = whisper.load_model(model_size if model_size in
        ("tiny", "base", "small", "medium", "large") else "small", device=device)
    res = model.transcribe(media_path, word_timestamps=True,
                           language=language, beam_size=beam_size)
    out = []
    for s in res.get("segments", []):
        words = [
            Word(float(w["start"]), float(w["end"]), str(w.get("word", "")).strip())
            for w in s.get("words", []) if str(w.get("word", "")).strip()
        ]
        out.append(Segment(float(s["start"]), float(s["end"]), s.get("text", "").strip(), words))
    return out


# --------------------------------------------------------------------------- #
# engine 2: OpenAI-compatible transcription API (no heavy deps on server)
# --------------------------------------------------------------------------- #
def transcribe_api(
    media_path: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "whisper-1",
    ffmpeg_bin: str | None = None,
    language: str | None = None,
) -> list[Segment]:
    from .editor import resolve_ffmpeg

    ff = ffmpeg_bin or resolve_ffmpeg()
    fd, wav = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        cmd = [ff, "-y", "-hide_banner", "-loglevel", "error",
               "-i", media_path, "-vn", "-ar", "16000", "-ac", "1",
               "-c:a", "pcm_s16le", wav]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"audio extraction failed: {proc.stderr[-1500:]}")
        if os.path.getsize(wav) > 25 * 1024 * 1024:
            raise RuntimeError(
                "Audio is larger than the 25MB API limit. Use local Whisper "
                "or subtitles for this video."
            )
        with open(wav, "rb") as f:
            audio = f.read()

        boundary = "----clipper" + os.urandom(8).hex()
        fields = {"model": model, "response_format": "verbose_json",
                  "timestamp_granularities[]": "word"}
        if language:
            fields["language"] = language
        body = bytearray()
        for k, v in fields.items():
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                 f"filename=\"audio.wav\"\r\nContent-Type: audio/wav\r\n\r\n").encode()
        body += audio + f"\r\n--{boundary}--\r\n".encode()

        req = urllib.request.Request(
            base_url.rstrip("/") + "/audio/transcriptions",
            data=bytes(body),
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    finally:
        if os.path.exists(wav):
            os.remove(wav)

    api_words = [
        Word(float(w["start"]), float(w["end"]), str(w.get("word", "")).strip())
        for w in data.get("words", []) if str(w.get("word", "")).strip()
    ]
    out = []
    for s in data.get("segments", []):
        st, en = float(s["start"]), float(s["end"])
        in_seg = [w for w in api_words if w.start >= st - 0.05 and w.start <= en + 0.05]
        out.append(Segment(st, en, s.get("text", "").strip(), in_seg or
                   _spread_words(s.get("text", ""), st, en)))
    return out


# --------------------------------------------------------------------------- #
# engine 3: subtitle files (word timing approximated per cue)
# --------------------------------------------------------------------------- #
_VTT_TS = re.compile(r"(\d+:)?(\d{1,2}):(\d{1,2})\.(\d{1,3})")
_TAG = re.compile(r"<[^>]+>")


def _vtt_ts(s: str) -> float:
    m = _VTT_TS.search(s.strip())
    if not m:
        return 0.0
    h = int(m.group(1)[:-1]) if m.group(1) else 0
    return h * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4).ljust(3, "0")) / 1000


def _spread_words(text: str, start: float, end: float) -> list[Word]:
    toks = [t for t in text.split() if t]
    if not toks or end <= start:
        return []
    weights = [len(t) + 1 for t in toks]
    total = sum(weights)
    words, t = [], start
    for i, tok in enumerate(toks):
        d = (end - start) * weights[i] / total
        words.append(Word(t, min(end, t + d) if i < len(toks) - 1 else end, tok))
        t += d
    return words


def vtt_to_segments(vtt_path: str) -> list[Segment]:
    with open(vtt_path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    blocks = re.split(r"\n\s*\n", content)
    out: list[Segment] = []
    for b in blocks:
        lines = [ln.strip() for ln in b.strip().splitlines() if ln.strip()]
        lines = [ln for ln in lines
                 if not ln.startswith(("WEBVTT", "NOTE", "STYLE", "REGION"))]
        if not lines:
            continue
        if "-->" not in lines[0]:  # cue identifier line present
            lines = lines[1:]
        if not lines or "-->" not in lines[0]:
            continue
        ts = lines[0].split("-->")
        start, end = _vtt_ts(ts[0]), _vtt_ts(ts[1])
        text = " ".join(_TAG.sub("", ln) for ln in lines[1:]).strip()
        if not text or end <= start:
            continue
        out.append(Segment(start, end, text, _spread_words(text, start, end)))
    out.sort(key=lambda s: s.start)
    return out
