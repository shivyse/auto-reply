"""Central configuration for the clipping automation. Everything is env-var driven
so it works the same locally, on Railway/Nixpacks, or inside the Telegram bot."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _list(name: str) -> list[str]:
    return [c.strip() for c in os.environ.get(name, "").split(",") if c.strip()]


@dataclass
class ClipperConfig:
    # --- clip selection ---
    clip_count: int = 3
    min_len: float = 20.0
    max_len: float = 55.0

    # --- rendering ---
    style: str = "crop"  # "crop" (full-bleed 9:16) or "blur" (fit + blurred bg)
    caption_font: str = "Anton"
    caption_fontsize: int = 92
    highlight: str = "yellow"  # yellow | green | cyan | pink
    ffmpeg_bin: str = ""

    # --- transcription ---
    # auto = video subtitles (free) -> local whisper -> OpenAI API, first that works
    transcribe_mode: str = "auto"  # auto | subs | local | api
    subs_lang: str = "en"
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute: str = "int8"

    # --- AI (OpenAI-compatible: OpenAI, Groq, Together, Gemini endpoint, ...) ---
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    use_llm: bool = True  # falls back to heuristics automatically when no key

    # --- paths ---
    work_dir: str = "clip_work"
    output_dir: str = "clips"

    # --- watcher (fully automatic mode) ---
    watch_channels: list[str] = field(default_factory=list)
    watch_interval_min: int = 15
    watch_state_file: str = "clip_watch_state.json"

    # --- YouTube auto-upload (optional) ---
    youtube_client_secrets: str = ""
    youtube_token_file: str = "youtube_token.json"
    youtube_privacy: str = "unlisted"  # unlisted | public | private

    @classmethod
    def from_env(cls) -> "ClipperConfig":
        return cls(
            clip_count=_int("CLIP_COUNT", 3),
            min_len=_float("CLIP_MIN_LEN", 20.0),
            max_len=_float("CLIP_MAX_LEN", 55.0),
            style=os.environ.get("CLIP_STYLE", "crop"),
            caption_font=os.environ.get("CAPTION_FONT", "Anton"),
            caption_fontsize=_int("CAPTION_FONTSIZE", 92),
            highlight=os.environ.get("CAPTION_HIGHLIGHT", "yellow"),
            ffmpeg_bin=os.environ.get("FFMPEG_BIN", ""),
            transcribe_mode=os.environ.get("TRANSCRIBE_MODE", "auto"),
            subs_lang=os.environ.get("SUBS_LANG", "en"),
            whisper_model=os.environ.get("WHISPER_MODEL", "small"),
            whisper_device=os.environ.get("WHISPER_DEVICE", "cpu"),
            whisper_compute=os.environ.get("WHISPER_COMPUTE", "int8"),
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            openai_base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            use_llm=os.environ.get("CLIP_NO_LLM", "") != "1",
            work_dir=os.environ.get("CLIP_WORK_DIR", "clip_work"),
            output_dir=os.environ.get("CLIP_OUTPUT_DIR", "clips"),
            watch_channels=_list("WATCH_CHANNELS"),
            watch_interval_min=_int("WATCH_INTERVAL_MIN", 15),
            watch_state_file=os.environ.get("WATCH_STATE_FILE", "clip_watch_state.json"),
            youtube_client_secrets=os.environ.get("YOUTUBE_CLIENT_SECRETS", ""),
            youtube_token_file=os.environ.get("YOUTUBE_TOKEN_FILE", "youtube_token.json"),
            youtube_privacy=os.environ.get("YOUTUBE_PRIVACY", "unlisted"),
        )
