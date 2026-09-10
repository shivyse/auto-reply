"""TikTok-style word-highlight captions rendered as ASS subtitles.

Each phrase is shown as a group; the word being spoken is highlighted in
color while the rest stays white — the classic viral caption look.
"""
from __future__ import annotations

from .transcriber import Word

# ASS colours are &HAABBGGRR
HIGHLIGHTS = {
    "yellow": "&H0000FFFF",
    "green": "&H0014FF39",
    "cyan": "&H00FFF000",
    "pink": "&H00A070FF",
    "orange": "&H000080FF",
}
WHITE = "&H00FFFFFF"


def chunk_words(words: list[Word], max_words: int = 4,
                max_span: float = 1.6, max_gap: float = 0.6) -> list[list[Word]]:
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words
                    or w.end - cur[0].start > max_span
                    or w.start - cur[-1].end > max_gap
                    or cur[-1].text.endswith((".", "!", "?", ","))):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def _fmt(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    cs = int(round((t - int(t)) * 100))
    if cs == 100:
        s += 1
        cs = 0
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def build_ass(words: list[Word], clip_start: float, clip_end: float,
              out_path: str, font: str = "Anton", fontsize: int = 92,
              highlight: str = "yellow") -> str:
    hl = HIGHLIGHTS.get(highlight, HIGHLIGHTS["yellow"])
    dur = max(0.5, clip_end - clip_start)
    rel = []
    for w in words:
        st, en = w.start - clip_start, w.end - clip_start
        if en <= 0 or st >= dur or not w.text.strip():
            continue
        rel.append(Word(max(0.0, st), min(dur, en), w.text.strip()))
    rel.sort(key=lambda w: w.start)

    events: list[str] = []
    for chunk in chunk_words(rel):
        mid = (len(chunk) + 1) // 2
        for i, w in enumerate(chunk):
            if i + 1 < len(chunk):
                end = chunk[i + 1].start - 0.02
            else:
                end = min(dur, w.end + 0.45)
            if end <= w.start + 0.06:
                end = min(dur, w.start + 0.22)
            toks = []
            for j, cw in enumerate(chunk):
                tok = _esc(cw.text.upper())
                toks.append(f"{{\\1c{hl}&\\b1}}{tok}{{\\1c{WHITE}&\\b1}}"
                            if j == i else tok)
            if len(toks) > 2:
                line = " ".join(toks[:mid]) + "\\N" + " ".join(toks[mid:])
            else:
                line = " ".join(toks)
            events.append(
                f"Dialogue: 0,{_fmt(w.start)},{_fmt(end)},Default,,0,0,0,,"
                f"{{\\an5\\pos(540,1330)}}{line}"
            )

    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n"
        "WrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, "
        "SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
        "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{font},{fontsize},&H00FFFFFF,&H000000FF,&H80000000,"
        "&H80000000,-1,0,0,0,100,100,2,0,1,3,2,5,40,40,120,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + ("\n" if events else ""))
    return out_path
