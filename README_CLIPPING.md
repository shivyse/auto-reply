# 🎬 Clipping Automation

Turn long videos into viral vertical shorts — automatically.

**Pipeline:** video URL or file → transcript → AI viral-moment detection →
9:16 captioned mp4s with titles + hashtags → delivered to Telegram (and
optionally auto-uploaded to YouTube Shorts).

```
YouTube / Twitch VOD / TikTok / upload
        │  yt-dlp
        ▼
  ┌─────────────┐   subtitles (free) ┌───────────┐
  │ Transcribe  │ ◄──────────────────┤ LLM picks │──► moments ──► ffmpeg ──► 📱 1080×1920
  └─────────────┘   local Whisper /  │  moments  │    cut·crop·captions·loudness
                    OpenAI API       └───────────┘
```

## What you got

| Mode | How |
|---|---|
| **On demand (Telegram)** | `/clip <video-URL> [count]` or send a video file |
| **Fully automatic** | Set `WATCH_CHANNELS` — every new upload gets clipped and sent to you |
| **CLI / script** | `python -m clipper.pipeline --url … --shorts 3` |
| **Auto-upload** | YouTube Shorts uploader included (needs one-time OAuth) |

No API key? It still works: YouTube subtitles + heuristic scoring are 100% free.
Add `OPENAI_API_KEY` and it upgrades to LLM moment-picking (works with OpenAI,
Groq, Together, Gemini's OpenAI endpoint, etc. via `OPENAI_BASE_URL`).

## Quick start (local)

```bash
pip install -r requirements.txt            # bot + downloading
pip install -r requirements-clipper.txt    # + local Whisper + YT upload (optional)
# ffmpeg must be installed:  sudo apt install ffmpeg   (or: pip install imageio-ffmpeg)

# 1. on-demand clip — subtitles mode is free, no keys needed
python -m clipper.pipeline --url "https://www.youtube.com/watch?v=XXXX" --shorts 3

# 2. from your own file, heuristic scoring only
python -m clipper.pipeline --file video.mp4 --no-llm

# 3. full AI mode (needs OPENAI_API_KEY)
export OPENAI_API_KEY=sk-...
python -m clipper.pipeline --url "https://..." --shorts 5
```

Clips land in `./clips/` with a `*_clips.json` file (titles, hooks, hashtags,
timestamps, scores).

## Telegram bot

The existing auto-reply bot now also clips. New commands:

- `/clip <video-URL> [count]` — e.g. `/clip https://youtu.be/xxxx 3`
- Send a **video file** — clips it directly (≤50MB via Telegram; bigger → send a link)
- `/help` — all commands

Clipping is admin-only by default; set `CLIP_ALLOW_ALL=1` to open it up.

## Fully automatic mode (watch channels)

```env
WATCH_CHANNELS=https://www.youtube.com/@SomeCreator,UCxxxxxxxxxxxxxxxxxxxxxx
WATCH_INTERVAL_MIN=15
ADMIN_CHAT_ID=123456789
```

The bot checks each channel's RSS feed and, for every **new** upload, runs the
whole pipeline and sends you the finished shorts. First run only baselines —
it won't spam-clip the back catalog. No YouTube API key needed for watching.

Optional auto-upload to YouTube Shorts: do the one-time OAuth on your machine,
then set `YOUTUBE_CLIENT_SECRETS` + `YOUTUBE_TOKEN_FILE`:

```bash
python -m clipper.uploader_youtube --auth --secrets client_secrets.json
```

## Configuration (env vars)

| Var | Default | Meaning |
|---|---|---|
| `CLIP_COUNT` | `3` | clips per video |
| `CLIP_MIN_LEN` / `CLIP_MAX_LEN` | `20` / `55` | clip length range (sec) |
| `CLIP_STYLE` | `crop` | `crop` full-bleed 9:16, or `blur` fit + blurred bg |
| `CAPTION_HIGHLIGHT` | `yellow` | active-word color: yellow/green/cyan/pink/orange |
| `CAPTION_FONT` / `CAPTION_FONTSIZE` | `Anton` / `92` | Anton auto-downloads once; DejaVu bundled as fallback |
| `TRANSCRIBE_MODE` | `auto` | `auto` → subs → local → api; or force `subs`/`local`/`api` |
| `SUBS_LANG` | `en` | subtitle language to fetch |
| `WHISPER_MODEL` | `small` | tiny/base/small/medium (local mode) |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | — | LLM picking + API transcription |
| `CLIP_NO_LLM` | — | set `1` to force heuristic scoring |
| `CLIP_WORK_DIR` / `CLIP_OUTPUT_DIR` | `clip_work` / `clips` | working + output folders |
| `FFMPEG_BIN` | auto | override ffmpeg path |
| `CLIP_ALLOW_ALL` | — | `1` = anyone can use /clip |
| `WATCH_CHANNELS` / `WATCH_INTERVAL_MIN` | — | auto mode (comma-separated) |
| `YOUTUBE_CLIENT_SECRETS` / `YOUTUBE_TOKEN_FILE` / `YOUTUBE_PRIVACY` | — | Shorts auto-upload |

## Deploy notes (Railway / Nixpacks)

- `nixpacks.toml` already includes `ffmpeg` + fonts — nothing to do.
- `requirements.txt` stays light (bot + yt-dlp). Transcription then uses
  **subtitles** (free) or the **OpenAI API** (`OPENAI_API_KEY`, ~$0.006/min).
- For free offline transcription on the server, install the full stack instead:
  change the install to `requirements-clipper.txt` (`faster-whisper` needs
  ~500MB RAM for the `small` model — set `WHISPER_MODEL=tiny` on small instances).
- Disk: videos + clips accumulate — `clip_work/` and `clips/` are git-ignored
  ephemeral storage; add a cron/volume cleanup for 24/7 operation.

## TikTok / Reels auto-posting?

- **YouTube Shorts**: supported (see above).
- **TikTok**: their Content Posting API needs an approved developer app + user
  OAuth; the pipeline gives you ready-to-post mp4s — wire `clips/*.mp4` into
  your TikTok app, or post from the Telegram delivery (download → post takes seconds).
- **Instagram Reels**: same story via the Graph API (business account + token).

## Project layout

```
clipper/
  pipeline.py      end-to-end job + CLI  (python -m clipper.pipeline ...)
  downloader.py    yt-dlp: video + subtitle fetching
  transcriber.py   local Whisper / API / subtitle transcripts (word timestamps)
  moments.py       LLM viral-moment picker + heuristic fallback
  captions.py      TikTok-style word-highlight ASS subtitles
  editor.py        ffmpeg: cut → 9:16 → burn captions → loudness normalize
  watcher.py       RSS channel monitor for fully-automatic mode
  uploader_youtube.py  YouTube Shorts upload (+ --auth helper)
  config.py        env-driven settings
  assets/          bundled fonts (Anton auto-fetches on first render)
tests/             unit tests — no network needed (python tests/test_clipper.py)
bot.py             Telegram bot: auto-reply + /clip + uploads + watcher
```

## Costs

- Subtitles + heuristics: **$0**
- LLM picking (`gpt-4o-mini` on a 10-min transcript): **~$0.01/video**
- API transcription (`whisper-1`): **~$0.006/min**
- Local Whisper (`small`, CPU): **$0**, ~0.3–1× realtime
