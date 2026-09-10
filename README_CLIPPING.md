# 🎬 Clipping Automation

Turn long videos into viral vertical shorts — automatically. Plus a **Whop
agent** that finds paid clipping campaigns and fulfills them for you.

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

## 💰 Whop agent (find campaigns → fulfill them)

The bot doubles as a **Whop Content Rewards** clipping agent: it scans the
marketplace for suitable paid campaigns, scores them by rate × remaining
budget, and produces compliant ready-to-post clips for the ones you pick.

```bash
python -m clipper.whop discover          # top suitable live campaigns
python -m clipper.whop show 1            # payouts, rules, reference links
python -m clipper.whop add <url>         # track a campaign you joined
python -m clipper.whop source <id> <youtube-url>   # footage to clip
python -m clipper.whop rules <id> <text> # paste full rules from inside Whop
python -m clipper.whop do <id> --count 3 # produce compliant clips + checklist
python -m clipper.whop posted <clip-id> <post-url>  # track submissions
```

Same thing in Telegram via `/whop discover|show|add|source|rules|do|posted|list`.

**How fulfillment works:** each campaign gets its footage clipped with the
campaign's own constraints auto-applied (min/max length, required hashtags,
mentions), clips land in `clips/whop_<id>/`, and you get a submission
checklist (where to post, what tags, where to submit the link). Progress is
tracked in `whop_state.json` (produced → posted → submitted).

**Filters (env):** `WHOP_MIN_RATE` (default 0.5), `WHOP_MIN_BUDGET_LEFT`
(1000), `WHOP_MAX_USED_PCT` (95), `WHOP_PLATFORMS` (e.g. `tiktok,youtube`),
`WHOP_NICHE_INCLUDE` / `WHOP_NICHE_EXCLUDE` keywords. Tip: skip campaigns
with nearly-dry budgets — late-verifying views can go unpaid.

**Honest scope:** posting must happen from *your* social accounts and link
submission happens inside Whop under your login, so those two steps stay
manual (~2 min/clip). The agent automates everything else: discovery,
economics, rules compliance, and clip production. Exception: if a campaign
allows YouTube and you've done the one-time Shorts OAuth, set
`WHOP_AUTO_UPLOAD=1` and fulfillment auto-publishes to your own channel.

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
  whop.py          Whop Content Rewards: discover, score, fulfill, track
  whop_bot.py      Telegram /whop subcommands
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
