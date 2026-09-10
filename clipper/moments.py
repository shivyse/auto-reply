"""Viral-moment detection.

Primary: an LLM watches the transcript and picks high-retention clips.
Fallback (no API key / API error): a deterministic heuristic scorer that looks
for hooks, questions, payoffs, numbers and emotional language.
"""
from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass, field

from .transcriber import Segment, prompt_text


@dataclass
class Moment:
    start: float
    end: float
    score: float = 0.0
    title: str = ""
    hook: str = ""
    hashtags: list[str] = field(default_factory=list)
    reason: str = ""


def pick_moments(
    segments: list[Segment],
    duration: float,
    count: int = 3,
    min_len: float = 20.0,
    max_len: float = 55.0,
    use_llm: bool = True,
    api_key: str = "",
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
) -> list[Moment]:
    if not segments:
        raise RuntimeError("Empty transcript — nothing to pick moments from.")
    duration = duration or max(s.end for s in segments)

    if use_llm and api_key:
        try:
            raw = _llm_moments(segments, duration, count, min_len, max_len,
                               api_key, base_url, model)
            moms = _finalize(raw, duration, min_len, max_len, count)
            if moms:
                print(f"[moments] LLM picked {len(moms)} moment(s)", flush=True)
                return moms
            print("[moments] LLM returned nothing usable, using heuristics", flush=True)
        except Exception as e:
            print(f"[moments] LLM failed ({e}), using heuristics", flush=True)
    else:
        print("[moments] no LLM key — using heuristic scoring", flush=True)
    return _heuristic_moments(segments, duration, count, min_len, max_len)


# --------------------------------------------------------------------------- #
# LLM picker (OpenAI-compatible chat completions, stdlib only — no extra dep)
# --------------------------------------------------------------------------- #
_SYSTEM = (
    "You are an expert short-form video editor for TikTok, Reels and YouTube Shorts. "
    "Given a timestamped transcript, pick the most viral-worthy moments. Each moment "
    "must hook the viewer in the first 2 seconds, deliver value or payoff, and work "
    "standalone without prior context. Reply with ONLY a JSON array, no markdown, no "
    "commentary. Each item: {\"start\": <seconds>, \"end\": <seconds>, "
    "\"title\": <short punchy title>, \"hook\": <first spoken line>, "
    "\"hashtags\": [\"#tag1\", ...], \"reason\": <why it will go viral>}."
)


def _llm_moments(segments, duration, count, min_len, max_len,
                 api_key, base_url, model) -> list[dict]:
    target = (min_len + max_len) / 2
    user = (
        f"Video duration: {duration:.1f} seconds.\n"
        f"Pick the {count} best clips. Each clip {min_len:.0f}-{max_len:.0f} seconds "
        f"(aim ~{target:.0f}s). Start times must be >= 0 and end times <= {duration:.1f}. "
        f"Spread picks across the video; do not overlap.\n\nTranscript:\n"
        f"{prompt_text(segments)}"
    )
    payload = {"model": model, "temperature": 0.7,
               "messages": [{"role": "system", "content": _SYSTEM},
                            {"role": "user", "content": user}]}
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    content = data["choices"][0]["message"]["content"].strip()
    content = re.sub(r"^```(?:json)?|```$", "", content.strip(),
                     flags=re.MULTILINE).strip()
    m = re.search(r"\[.*\]", content, flags=re.DOTALL)
    items = json.loads(m.group(0) if m else content)
    if isinstance(items, dict):  # some models wrap in {"clips": [...]}
        for v in items.values():
            if isinstance(v, list):
                items = v
                break
    return items if isinstance(items, list) else []


def _finalize(raw: list[dict], duration: float, min_len: float,
              max_len: float, count: int) -> list[Moment]:
    moms: list[Moment] = []
    for r in raw:
        try:
            start = max(0.0, float(r["start"]))
            end = min(duration, float(r["end"]))
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        if end - start < min_len:  # extend short picks
            end = min(duration, start + min_len)
            if end - start < min_len:
                start = max(0.0, end - min_len)
        if end - start > max_len:
            end = start + max_len
        tags = [t if t.startswith("#") else f"#{t}"
                for t in (r.get("hashtags") or [])][:6]
        moms.append(Moment(round(start, 2), round(end, 2),
                           score=float(r.get("score", 50)),
                           title=str(r.get("title", ""))[:100],
                           hook=str(r.get("hook", ""))[:200],
                           hashtags=tags,
                           reason=str(r.get("reason", ""))[:300]))
    moms.sort(key=lambda m: m.score, reverse=True)
    picked: list[Moment] = []
    for m in moms:
        if all(_overlap(m, p) / min(m.end - m.start, p.end - p.start) < 0.4
               for p in picked):
            picked.append(m)
        if len(picked) >= count:
            break
    return picked


def _overlap(a: Moment, b: Moment) -> float:
    return max(0.0, min(a.end, b.end) - max(a.start, b.start))


# --------------------------------------------------------------------------- #
# heuristic fallback
# --------------------------------------------------------------------------- #
_HOOK_PHRASES = [
    "nobody talks about", "nobody tells you", "stop doing", "never do",
    "secret", "free", "mistake", "truth", "lie", "exposed", "warning",
    "watch this", "listen", "here's why", "here is why", "this is why",
    "nobody knows", "what if", "imagine", "believe it or not", "proof",
    "guarantee", "insane", "crazy", "shocking", "viral", "million",
    "quit", "broke", "rich", "money", "hack", "trick", "tutorial",
    "step by step", "in seconds", "nobody", "everyone", "always", "never",
    "actually", "honestly", "worst", "best", "biggest", "first time",
]
_CONTRAST = ["but ", "however", "although", "instead", "until ", " plot twist",
             "turns out", "the catch", "the problem is"]
_POWER = ["love", "hate", "fear", "angry", "cry", "laugh", "win", "lose",
          "fail", "success", "amazing", "terrible", "unbelievable", "impossible",
          "easy", "hard", "fast", "slow", "old", "new", "big", "small"]
_STOPWORDS = set("""a an the and or but if then so than too very can will just don should now
with from that this these those you your yours he she they them his her its our we us i me my mine
me im ive dont didnt doesnt isnt was were are is be been being have has had do does did not no yes
of on in to for at as by up out over into after before during over under about what when where who
whom which why how all any both each few more most other some such only own same so than very can
will just don should now""".split())


def _sentences(segments: list[Segment]) -> list[dict]:
    sents: list[dict] = []
    buf: list[tuple[float, float, str]] = []

    def flush():
        if not buf:
            return
        text = " ".join(t for _, _, t in buf).strip()
        if text:
            sents.append({"start": buf[0][0], "end": buf[-1][1], "text": text})
        buf.clear()

    for s in segments:
        toks = s.words or []
        if not toks:  # segment-level fallback
            for part in re.split(r"(?<=[.!?…])\s+", s.text.strip()):
                if part:
                    sents.append({"start": s.start, "end": s.end, "text": part})
            continue
        for w in toks:
            buf.append((w.start, w.end, w.text))
            if re.search(r"[.!?…]$", w.text):
                flush()
        flush()
    return sents


def _sent_score(text: str) -> tuple[float, list[str]]:
    t = text.lower()
    score, hits = 0.0, []
    for p in _HOOK_PHRASES:
        if p in t:
            score += 4.0
            hits.append(p)
            if len(hits) >= 3:
                break
    for p in _CONTRAST:
        if p in t:
            score += 1.5
            hits.append(p.strip())
            break
    pw = sum(1 for p in _POWER if re.search(rf"\b{re.escape(p)}\b", t))
    score += min(pw, 3) * 1.0
    if "?" in text:
        score += 2.0
        hits.append("question")
    if "!" in text:
        score += 2.0
    if re.search(r"\d", text):
        score += 1.0
    if re.search(r"\b(you|your|yours)\b", t):
        score += 1.0
    caps = sum(1 for w in text.split() if w.isupper() and len(w) > 2)
    score += min(caps, 2) * 0.5
    n = len(text.split())
    if 6 <= n <= 30:
        score += 1.0
    return score, hits


def _keywords(text: str, limit: int = 4) -> list[str]:
    freq: dict[str, int] = {}
    for w in re.findall(r"[A-Za-z][A-Za-z0-9_]{3,}", text):
        wl = w.lower()
        if wl not in _STOPWORDS:
            freq[wl] = freq.get(wl, 0) + 1
    ranked = sorted(freq, key=lambda w: (freq[w], len(w)), reverse=True)
    return [f"#{w}" for w in ranked[:limit]]


def _heuristic_moments(segments, duration, count, min_len, max_len) -> list[Moment]:
    sents = _sentences(segments)
    if not sents:
        raise RuntimeError("Could not extract sentences from transcript.")
    target = (min_len + max_len) / 2
    scored = [(s, *_sent_score(s["text"])) for s in sents]
    cands: list[Moment] = []
    n = len(scored)
    for i in range(n):
        total, hits, text_parts = 0.0, [], []
        for j in range(i, min(n, i + 60)):
            s, sc, h = scored[j]
            total += sc
            hits += h
            text_parts.append(s["text"])
            dur = s["end"] - scored[i][0]["start"]
            if dur < min_len - 4:
                continue
            if dur > max_len + 8:
                break
            first = scored[i][0]["text"]
            bonus = 3.0 if _sent_score(first)[0] >= 4 else 0.0  # strong hook opening
            length_fit = max(0.0, 3.0 - abs(dur - target) / 8.0)
            score = total + bonus + length_fit + (1.0 if dur >= min_len else -2.0)
            joined = " ".join(text_parts)
            title = (first[:70] + "…") if len(first) > 70 else first
            cands.append(Moment(
                start=round(max(0.0, scored[i][0]["start"] - 0.15), 2),
                end=round(min(duration, s["end"] + 0.25), 2),
                score=round(score, 2), title=title,
                hook=first[:200],
                hashtags=_keywords(joined) + ["#shorts", "#fyp", "#viral"],
                reason=f"heuristic score {score:.1f}" +
                       (f" (hooks: {', '.join(sorted(set(hits))[:4])})" if hits else ""),
            ))
    if not cands:
        # very short video: take the whole thing as one clip
        cands = [Moment(0.0, round(duration, 2), score=1.0, title="Full clip",
                        hashtags=["#shorts", "#fyp", "#viral"],
                        reason="video shorter than min clip length")]
    cands.sort(key=lambda m: m.score, reverse=True)
    picked: list[Moment] = []
    for m in cands:
        if len(picked) >= count:
            break
        span = m.end - m.start
        if span < 5:
            continue
        if all(_overlap(m, p) / min(span, p.end - p.start) < 0.4 for p in picked):
            picked.append(m)
    # enforce min/max length on heuristic windows
    for m in picked:
        if m.end - m.start < min_len:
            m.end = round(min(duration, m.start + min_len), 2)
            if m.end - m.start < min_len:
                m.start = round(max(0.0, m.end - min_len), 2)
        if m.end - m.start > max_len:
            m.end = round(m.start + max_len, 2)
    print(f"[moments] heuristic picked {len(picked)} moment(s)", flush=True)
    return picked
