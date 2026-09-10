"""Whop Content Rewards integration: find suitable clipping campaigns and fulfill them.

    python -m clipper.whop discover              # list suitable live campaigns
    python -m clipper.whop show <url|id|num>     # campaign details + rules
    python -m clipper.whop add <url>             # track a campaign you joined
    python -m clipper.whop do <id>               # produce ready-to-post clips

Flow: discover -> score by rate x budget -> fulfill (compliant clips +
submission checklist) -> you post + submit the link -> track status.

What is automated: finding campaigns, reading their economics/rules, and
producing compliant, captioned, ready-to-post clips.
What stays manual: posting from YOUR social accounts and pasting the post
link into Whop (their login + your accounts; 2 minutes per clip).
Exception: YouTube Shorts CAN auto-post to your own channel once you've
done the one-time OAuth (see uploader_youtube.py) + WHOP_AUTO_UPLOAD=1.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass, field, asdict
from html.parser import HTMLParser

DISCOVER_URL = "https://contentrewards.com/discover"
_CAMPAIGN_RE = re.compile(r"/discover/([0-9a-fA-F-]{36})")
_UUID_RE = re.compile(r"[0-9a-fA-F-]{36}")


# --------------------------------------------------------------------------- #
# data model
# --------------------------------------------------------------------------- #
@dataclass
class Payout:
    platform: str  # tiktok | instagram | youtube | x
    rate_per_1k: float = 0.0
    min_payout: float = 0.0
    max_payout: float = 0.0


@dataclass
class Campaign:
    id: str
    title: str = ""
    brand: str = ""
    url: str = ""
    join_url: str = ""
    description: str = ""
    rate_per_1k: float = 0.0          # headline rate
    budget_total: float = 0.0
    budget_spent: float = 0.0
    creators: int = 0
    payouts: list[Payout] = field(default_factory=list)
    reference_links: list[dict] = field(default_factory=list)  # {label, url}
    sources: list[str] = field(default_factory=list)  # footage URLs (user-added or resolved)
    rules_text: str = ""              # full rules (user-pasted after joining)
    hashtags: list[str] = field(default_factory=list)
    status: str = "new"               # new | watching | joined | active | paused | done
    clips: list[dict] = field(default_factory=list)
    fetched_at: float = 0.0
    score: float = 0.0
    score_reasons: list[str] = field(default_factory=list)

    @property
    def budget_left(self) -> float:
        return max(0.0, self.budget_total - self.budget_spent)

    @property
    def pct_used(self) -> float:
        if not self.budget_total:
            return 0.0
        return 100.0 * self.budget_spent / self.budget_total

    @property
    def best_rate(self) -> float:
        rates = [p.rate_per_1k for p in self.payouts if p.rate_per_1k] + [self.rate_per_1k]
        return max(rates) if rates else 0.0

    @property
    def platforms(self) -> list[str]:
        return [p.platform for p in self.payouts]

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Campaign":
        d = dict(d)
        d["payouts"] = [p if isinstance(p, Payout) else Payout(**p)
                        for p in d.get("payouts", [])]
        d.pop("score_reasons", None)
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known},
                   score_reasons=d.get("score_reasons", []))


@dataclass
class WhopPrefs:
    min_rate: float = 0.5
    min_budget_left: float = 1000.0
    max_used_pct: float = 95.0
    platforms: list[str] = field(default_factory=list)  # empty = any
    include: list[str] = field(default_factory=list)    # niche keywords (any match boosts)
    exclude: list[str] = field(default_factory=list)    # keyword blacklist
    state_file: str = "whop_state.json"

    @classmethod
    def from_env(cls) -> "WhopPrefs":
        def _f(name, default):
            try:
                return float(os.environ.get(name, default))
            except (TypeError, ValueError):
                return default

        def _l(name):
            return [x.strip().lower() for x in os.environ.get(name, "").split(",") if x.strip()]

        return cls(
            min_rate=_f("WHOP_MIN_RATE", 0.5),
            min_budget_left=_f("WHOP_MIN_BUDGET_LEFT", 1000.0),
            max_used_pct=_f("WHOP_MAX_USED_PCT", 95.0),
            platforms=_l("WHOP_PLATFORMS"),
            include=_l("WHOP_NICHE_INCLUDE"),
            exclude=_l("WHOP_NICHE_EXCLUDE"),
            state_file=os.environ.get("WHOP_STATE_FILE", "whop_state.json"),
        )


# --------------------------------------------------------------------------- #
# fetching + parsing (stdlib only)
# --------------------------------------------------------------------------- #
def fetch_html(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", "replace")


class _TextLinks(HTMLParser):
    """Extract visible text plus (anchor-text, href) links."""

    def __init__(self):
        super().__init__()
        self.chunks: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._atext: list[str] = []
        self._skip = 0  # inside script/style

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        if tag == "a" and self._skip == 0:
            href = dict(attrs).get("href", "")
            self._href = href
            self._atext = []
        if tag in ("br", "p", "div", "h1", "h2", "h3", "h4", "li", "tr") and self._skip == 0:
            self.chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
        if tag == "a" and self._href is not None:
            self.links.append((" ".join("".join(self._atext).split()), self._href))
            self._href = None

    def handle_data(self, data):
        if self._skip:
            return
        self.chunks.append(data)
        if self._href is not None:
            self._atext.append(data)

    def text(self) -> str:
        import html as _html
        return _html.unescape("".join(self.chunks))


def parse_money(s: str) -> float:
    """'$39.5K' -> 39500, '$2.5K' -> 2500, '$3.50' -> 3.5."""
    s = s.strip().replace("$", "").replace(",", "")
    m = re.match(r"(\d[\d.]*)([kKmM]?)", s)
    if not m:
        return 0.0
    try:
        val = float(m.group(1))
    except ValueError:
        return 0.0
    suffix = m.group(2).lower()
    if suffix == "k":
        val *= 1000.0
    elif suffix == "m":
        val *= 1_000_000.0
    return val


def _parse_count(s: str) -> int:
    return int(parse_money(s))


def _next_data_campaigns(html: str) -> list[dict]:
    """Best-effort: pull campaign objects out of Next.js __NEXT_DATA__ blob."""
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                  html, flags=re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []

    found: list[dict] = []

    def walk(o):
        if isinstance(o, dict):
            keys = {k.lower() for k in o}
            if ("rateperthousand" in keys or "rate_per_1k" in keys
                    or "budgettotal" in keys) and ("title" in keys or "name" in keys):
                found.append(o)
                return
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    return found


def _campaign_from_nextdata(o: dict) -> Campaign:
    g = lambda *names: next((o[k] for k in o if k.lower() in names), None)
    cid = str(g("id", "campaignid", "uuid") or "")
    if not _UUID_RE.fullmatch(cid):
        m = _UUID_RE.search(cid)
        cid = m.group(0) if m else cid
    title = str(g("title", "name") or "")
    brand = ""
    org = g("organization", "brand", "org")
    if isinstance(org, dict):
        brand = str(org.get("name", "") or "")
    rate = float(g("rateperthousand", "rate_per_1k", "rate") or 0)
    total = float(g("budgettotal", "totalbudget", "budget") or 0)
    spent = float(g("budgetspent", "spentbudget", "spent") or 0)
    creators = int(g("creators", "creatorscount", "joined") or 0)
    desc = str(g("description", "about") or "")
    return Campaign(id=cid, title=title, brand=brand,
                    url=f"{DISCOVER_URL}/{cid}" if cid else "",
                    description=desc[:2000], rate_per_1k=rate,
                    budget_total=total, budget_spent=spent,
                    creators=creators, fetched_at=time.time())


def parse_discover_html(html: str, limit: int = 20) -> list[Campaign]:
    """Parse the /discover marketplace page into lite campaigns."""
    out: list[Campaign] = []
    seen: set[str] = set()
    for o in _next_data_campaigns(html):
        try:
            c = _campaign_from_nextdata(o)
        except (ValueError, TypeError):
            continue
        if c.id and c.id not in seen:
            seen.add(c.id)
            out.append(c)
    if out:
        return out[:limit]

    # fallback: link + text-window parsing
    parser = _TextLinks()
    parser.feed(html)
    text = parser.text()
    ids: list[str] = []
    for _, href in parser.links:
        m = _CAMPAIGN_RE.search(href or "")
        if m and m.group(1) not in ids:
            ids.append(m.group(1))
    for cid in ids[:limit]:
        # find a text window around the campaign's link/title mention
        c = Campaign(id=cid, url=f"{DISCOVER_URL}/{cid}", fetched_at=time.time())
        out.append(c)
    # Rate/budget/creator signals appear per-card in order; attach greedily.
    rates = [float(x) for x in re.findall(r"\$([\d.]+)\s*/\s*1[Kk]", text)]
    budgets = re.findall(r"\$(\d[\d.,]*[kKmM]?)\s*/\s*\$(\d[\d.,]*[kKmM]?)", text)
    joins = re.findall(r"(\d[\d.,]*[kKmM]?)\s*(?:joined|creators)", text,
                       flags=re.IGNORECASE)
    for i, c in enumerate(out):
        if i < len(rates):
            c.rate_per_1k = rates[i]
        if i < len(budgets):
            c.budget_spent = parse_money(budgets[i][0])
            c.budget_total = parse_money(budgets[i][1])
        if i < len(joins):
            c.creators = _parse_count(joins[i])
    return out


def parse_campaign_html(html: str, url: str = "") -> Campaign:
    """Parse a campaign detail page: economics, payouts, references, join link."""
    m = _CAMPAIGN_RE.search(url) or _UUID_RE.search(html[:5000])
    cid = m.group(1) if m and "/" in (m.group(0) or "") else (m.group(0) if m else "")
    parser = _TextLinks()
    parser.feed(html)
    text = parser.text()
    one_line = " ".join(text.split())

    title = ""
    tm = re.search(r"<title>(.*?)</title>", html, flags=re.DOTALL | re.IGNORECASE)
    if tm:
        import html as _html
        title = _html.unescape(tm.group(1)).split("|")[0].split(" by ")[0].strip()

    # economics
    rate = 0.0
    rm = re.search(r"\$([\d.]+)\s*/\s*1[Kk]", one_line)
    if rm:
        rate = float(rm.group(1))
    spent = total = 0.0
    bm = re.search(r"\$(\d[\d.,]*[kKmM]?)\s*/\s*\$(\d[\d.,]*[kKmM]?)", one_line)
    if bm:
        spent, total = parse_money(bm.group(1)), parse_money(bm.group(2))
    creators = 0
    cm = re.search(r"(?:Creators|Joined)\s*(\d[\d.,]*[kKmM]?)"
                   r"|(\d[\d.,]*[kKmM]?)\s*(?:Creators|joined)",
                   one_line, flags=re.IGNORECASE)
    if cm:
        creators = _parse_count(cm.group(1) or cm.group(2))

    # per-platform payout table
    payouts: list[Payout] = []
    for pm in re.finditer(
            r"(tiktok|instagram|youtube|\bx\b|twitter)\s*\$([\d.]+)\s*per 1k views"
            r"(?:\s*\$(\d[\d.,]*[kKmM]?)\s*min)?(?:\s*\$(\d[\d.,]*[kKmM]?)\s*max)?",
            one_line, flags=re.IGNORECASE):
        plat = pm.group(1).lower()
        plat = {"x": "x", "twitter": "x"}.get(plat, plat)
        payouts.append(Payout(platform=plat, rate_per_1k=float(pm.group(2)),
                              min_payout=parse_money(pm.group(3) or "0"),
                              max_payout=parse_money(pm.group(4) or "0")))

    # description: text between budget marker and first payout mention
    desc = ""
    dm = re.search(r"% used\s*(.+?)\s*(?:TikTok|Instagram|YouTube|\bX\b)\s*\$",
                   one_line, flags=re.IGNORECASE)
    if dm:
        desc = dm.group(1).strip()[:2000]

    # join URL + reference material links
    join_url = ""
    refs: list[dict] = []
    for label, href in parser.links:
        if not href or href.startswith(("#", "/_next", "/signup")):
            continue
        if "/experiences/" in href and "/campaigns/" in href and not join_url:
            join_url = href if href.startswith("http") else f"https://whop.com{href}"
            continue
        if href.startswith("http") and not any(
                d in href for d in ("contentrewards.com", "s3.", "amazonaws.com")):
            if re.search(r"\.(jpg|jpeg|png|webp|gif|svg|css|js)(\?|$)", href,
                         flags=re.IGNORECASE):
                continue
            if href not in [r["url"] for r in refs]:
                refs.append({"label": label[:80] or href[:80], "url": href})
    refs = refs[:15]

    return Campaign(id=cid, title=title, url=url, join_url=join_url,
                    description=desc, rate_per_1k=rate,
                    budget_total=total, budget_spent=spent, creators=creators,
                    payouts=payouts, reference_links=refs, fetched_at=time.time())


def fetch_campaign(url: str) -> Campaign:
    return parse_campaign_html(fetch_html(url), url)


def discover(limit: int = 15, enrich: int = 0) -> list[Campaign]:
    """Fetch the marketplace board. enrich=N fetches full detail for top N."""
    cards = parse_discover_html(fetch_html(DISCOVER_URL), limit)
    # resolve titles etc. via detail pages for the most promising cards
    cards.sort(key=lambda c: c.rate_per_1k, reverse=True)
    for c in cards[:max(0, enrich)]:
        try:
            full = fetch_campaign(c.url)
            if full.title:
                c.title, c.brand = full.title, full.brand
            for attr in ("join_url", "description", "rate_per_1k", "budget_total",
                         "budget_spent", "creators", "payouts", "reference_links"):
                v = getattr(full, attr)
                if v:
                    setattr(c, attr, v)
        except Exception as e:
            print(f"[whop] enrich failed for {c.id}: {e}", flush=True)
    return cards


# --------------------------------------------------------------------------- #
# rules parsing (campaign requirements -> clip constraints + checklist)
# --------------------------------------------------------------------------- #
def parse_rules(text: str) -> dict:
    t = " ".join((text or "").split())
    rules: dict = {"hashtags": [], "mentions": [], "min_len": None,
                   "max_len": None, "platforms": [], "banned": [], "notes": []}
    rules["hashtags"] = sorted({h for h in re.findall(r"#(\w+)", t)})[:10]
    rules["hashtags"] = [f"#{h}" for h in rules["hashtags"]]
    rules["mentions"] = sorted({f"@{x.rstrip('.')}" for x in
                                re.findall(r"(?:^|\s)@([A-Za-z0-9_.]{2,30})", t)})[:10]
    m = re.search(r"(?:at least|minimum|over)\s*(\d+)\s*(?:s|sec|seconds?)", t,
                  flags=re.IGNORECASE)
    if m:
        rules["min_len"] = float(m.group(1))
    m = re.search(r"(?:under|below|maximum|up to|less than|max)\s*(\d+)\s*(?:s|sec|seconds?)",
                  t, flags=re.IGNORECASE)
    if m:
        rules["max_len"] = float(m.group(1))
    m = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*(?:s|sec|seconds?)", t)
    if m:
        rules["min_len"] = rules["min_len"] or float(m.group(1))
        rules["max_len"] = rules["max_len"] or float(m.group(2))
    for plat in ("tiktok", "instagram", "reels", "youtube", "shorts", "twitter", " x "):
        if plat.strip() in t.lower():
            name = {"reels": "instagram", "shorts": "youtube",
                    "twitter": "x", "x": "x"}.get(plat.strip(), plat.strip())
            if name not in rules["platforms"]:
                rules["platforms"].append(name)
    for sent in re.split(r"(?<=[.!])\s+", t):
        s = sent.strip()
        if len(s) > 12 and re.search(r"\b(do not|don't|never|no |without|must not|avoid)\b",
                                     s, flags=re.IGNORECASE):
            rules["banned"].append(s[:160])
    rules["banned"] = rules["banned"][:8]
    return rules


# --------------------------------------------------------------------------- #
# suitability scoring
# --------------------------------------------------------------------------- #
def score_campaign(c: Campaign, prefs: WhopPrefs) -> Campaign:
    reasons: list[str] = []
    blob = f"{c.title} {c.brand} {c.description}".lower()
    if any(x in blob for x in prefs.exclude):
        c.score, c.score_reasons = 0.0, ["excluded keyword"]
        return c
    rate = c.best_rate
    if rate < prefs.min_rate:
        c.score, c.score_reasons = 0.0, [f"rate ${rate}/1k < ${prefs.min_rate} min"]
        return c
    if c.budget_total and c.budget_left < prefs.min_budget_left:
        c.score, c.score_reasons = 0.0, [f"budget left ${c.budget_left:,.0f} too low"]
        return c
    if c.pct_used > prefs.max_used_pct:
        c.score, c.score_reasons = 0.0, [f"budget {c.pct_used:.0f}% used"]
        return c
    if prefs.platforms and c.platforms and not set(c.platforms) & set(prefs.platforms):
        c.score, c.score_reasons = 0.0, ["no matching platform"]
        return c

    budget_factor = 0.5 + 0.5 * min(1.0, c.budget_left / 50000.0) if c.budget_total else 0.75
    score = rate * 10.0 * budget_factor
    reasons.append(f"${rate}/1k")
    if c.budget_total:
        reasons.append(f"${c.budget_left:,.0f} left ({c.pct_used:.0f}% used)")
    if prefs.platforms and set(c.platforms) & set(prefs.platforms):
        score *= 1.2
        reasons.append("platform match")
    if prefs.include and any(x in blob for x in prefs.include):
        score *= 1.15
        reasons.append("niche match")
    if c.creators:
        score *= 1.0 + min(0.1, c.creators / 50000.0)
    c.score, c.score_reasons = round(score, 2), reasons
    return c


def suitable(campaigns: list[Campaign], prefs: WhopPrefs) -> list[Campaign]:
    for c in campaigns:
        score_campaign(c, prefs)
    return sorted([c for c in campaigns if c.score > 0],
                  key=lambda c: c.score, reverse=True)


# --------------------------------------------------------------------------- #
# state store
# --------------------------------------------------------------------------- #
def load_state(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data.setdefault("campaigns", {})
                data.setdefault("last_discover", [])
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"campaigns": {}, "last_discover": []}


def save_state(state: dict, path: str) -> None:
    state["updated_at"] = time.time()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def upsert_campaign(state: dict, c: Campaign) -> None:
    prev = state["campaigns"].get(c.id, {})
    d = c.to_dict()
    for keep in ("status", "sources", "rules_text", "clips", "hashtags"):
        if keep in prev and not d.get(keep):
            d[keep] = prev[keep]
    if prev.get("status") not in (None, "", "new"):
        d["status"] = prev["status"]
    state["campaigns"][c.id] = d


def resolve_ref(state: dict, ref: str) -> str | None:
    """Resolve a campaign ref: full id, id prefix, discover URL, or 1-based index."""
    ref = ref.strip()
    m = _CAMPAIGN_RE.search(ref) or _UUID_RE.search(ref)
    if m:
        cid = m.group(1) if m.lastindex else m.group(0)
        if cid in state["campaigns"]:
            return cid
        for k in state["campaigns"]:
            if k.lower().startswith(cid.lower()):
                return k
        return cid  # unknown yet — caller may fetch it
    if ref.isdigit():
        idx = int(ref) - 1
        ids = state.get("last_discover", [])
        if 0 <= idx < len(ids):
            return ids[idx]
    for k in state["campaigns"]:
        if k.lower().startswith(ref.lower()):
            return k
    return None


def get_campaign(state: dict, cid: str) -> Campaign | None:
    d = state["campaigns"].get(cid)
    return Campaign.from_dict(d) if d else None


# --------------------------------------------------------------------------- #
# fulfillment: campaign -> compliant clips
# --------------------------------------------------------------------------- #
def _merge_hashtags(clips: list[dict], forced: list[str]) -> None:
    for clip in clips:
        tags = clip.get("hashtags", []) + [t for t in forced if t not in clip.get("hashtags", [])]
        clip["hashtags"] = tags[:10]


def fulfill(cid: str, prefs: WhopPrefs, count: int | None = None,
            sources: list[str] | None = None, run_job_fn=None,
            cfg=None) -> dict:
    """Run clip jobs for a tracked campaign. Returns summary + checklist."""
    from .config import ClipperConfig
    from .pipeline import run_job

    run_job_fn = run_job_fn or run_job
    cfg = cfg or ClipperConfig.from_env()
    state = load_state(prefs.state_file)
    camp = get_campaign(state, cid)
    if not camp:
        raise ValueError(f"unknown campaign: {cid} (use /whop add <url> first)")

    srcs = sources or camp.sources
    if not srcs:
        refs = "\n".join(f"• {r['label']}: {r['url']}" for r in camp.reference_links[:8])
        raise ValueError(
            f"No source footage configured for '{camp.title or cid}'.\n"
            f"Add the creator's video/channel links:\n"
            f"  Telegram: /whop source {cid[:8]} <youtube-url> [...]\n"
            f"  CLI: python -m clipper.whop source {cid} <url>\n" +
            (f"\nCampaign reference materials (may list sources):\n{refs}" if refs else ""))

    rules = parse_rules(f"{camp.description}\n{camp.rules_text}")
    forced_tags = sorted(set(camp.hashtags + rules["hashtags"]))
    min_len = rules["min_len"] or cfg.min_len
    max_len = rules["max_len"] or cfg.max_len
    if min_len >= max_len:
        min_len, max_len = cfg.min_len, cfg.max_len
    count = count or cfg.clip_count
    short = camp.id[:8]
    out_dir = os.path.join(cfg.output_dir, f"whop_{short}")
    from dataclasses import replace
    cfg = replace(cfg, min_len=min_len, max_len=max_len, output_dir=out_dir)

    made: list[dict] = []
    for i, src in enumerate(srcs):
        is_url = src.startswith("http")
        job = run_job_fn(url=src if is_url else None,
                         file_path=None if is_url else src,
                         cfg=cfg, count=count)
        _merge_hashtags(job["clips"], forced_tags)
        for clip in job["clips"]:
            clip["clip_id"] = f"{short}_c{len(camp.clips) + len(made) + 1}"
            clip["status"] = "produced"
            clip["post_url"] = ""
            made.append(clip)

    camp.clips.extend(made)
    if camp.status in ("new", "watching"):
        camp.status = "active"
    upsert_campaign(state, camp)
    save_state(state, prefs.state_file)

    # optional YouTube auto-upload to the user's own channel
    uploaded: list[str] = []
    if os.environ.get("WHOP_AUTO_UPLOAD", "") == "1":
        from .uploader_youtube import upload_short
        for clip in made:
            try:
                uploaded.append(upload_short(
                    clip["path"], clip["title"],
                    description=f"{clip.get('hook', '')}\n\n{' '.join(clip.get('hashtags', []))}",
                    tags=[t.lstrip("#") for t in clip.get("hashtags", [])],
                    privacy="public"))
                clip["status"] = "posted"
            except Exception as e:
                clip["upload_error"] = str(e)[:200]
        upsert_campaign(state, camp)
        save_state(state, prefs.state_file)

    econ = _econ_line(camp)
    checklist = _checklist(camp, rules, forced_tags, uploaded)
    return {"campaign": camp.to_dict(), "clips": made, "econ": econ,
            "checklist": checklist, "uploaded": uploaded}


def _money(v: float) -> str:
    return f"${v:,.0f}" if v >= 100 else f"${v:g}"


def _econ_line(c: Campaign) -> str:
    if c.payouts:
        parts = [f"{p.platform.title()} ${p.rate_per_1k:g}/1k" +
                 (f" (per-post {_money(p.min_payout)}–{_money(p.max_payout)})"
                  if p.max_payout else "")
                 for p in c.payouts]
        econ = " · ".join(parts)
    else:
        econ = f"${c.best_rate}/1k views"
    if c.budget_total:
        econ += f" · budget left ${c.budget_left:,.0f}"
    return econ


def _checklist(c: Campaign, rules: dict, tags: list[str], uploaded: list[str]) -> str:
    plats = rules["platforms"] or c.platforms or ["tiktok"]
    lines = [f"💰 {c.title or c.id}", _econ_line(c), "",
             "📋 To earn:"]
    if uploaded:
        lines.append("1. ✅ Auto-posted to your YouTube (public):")
        lines += [f"   {u}" for u in uploaded]
        step = 2
    else:
        lines.append(f"1. Post each clip to: {', '.join(p.title() for p in plats)}")
        step = 2
    if tags:
        lines.append(f"{step}. Use hashtags: {' '.join(tags)}")
        step += 1
    if rules["mentions"]:
        lines.append(f"{step}. Tag: {' '.join(rules['mentions'])}")
        step += 1
    for b in rules["banned"][:4]:
        lines.append(f"{step}. ⚠️ {b}")
        step += 1
    join = c.join_url or c.url
    if join:
        lines.append(f"{step}. Submit your post links here: {join}")
        step += 1
    lines.append(f"{step}. Track: /whop posted <clip-id> <post-url>")
    return "\n".join(lines)


def campaign_card(c: Campaign, idx: int | None = None) -> str:
    prefix = f"{idx}. " if idx is not None else ""
    lines = [f"{prefix}{c.title or c.id}"]
    if c.brand:
        lines[-1] += f" — {c.brand}"
    lines.append(f"   💰 {_econ_line(c)} · 👥 {c.creators or '?'} clippers")
    if c.score:
        lines.append(f"   ⭐ score {c.score} ({', '.join(c.score_reasons)})")
    if c.url:
        lines.append(f"   🔗 {c.url}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# curated campaigns file (campaigns you've joined, with sources pre-filled)
# --------------------------------------------------------------------------- #
def load_curated(path: str) -> list[Campaign]:
    """Load hand-written campaign JSON: [{title, url, sources:[...], rules_text...}]."""
    if not path or not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out = []
    for d in raw if isinstance(raw, list) else []:
        m = _UUID_RE.search(d.get("url", "") or "")
        cid = d.get("id") or (m.group(0) if m else d.get("title", "")[:32])
        out.append(Campaign(id=cid, title=d.get("title", ""), brand=d.get("brand", ""),
                            url=d.get("url", ""), join_url=d.get("join_url", ""),
                            description=d.get("description", ""),
                            rate_per_1k=float(d.get("rate_per_1k", 0)),
                            budget_total=float(d.get("budget_total", 0)),
                            budget_spent=float(d.get("budget_spent", 0)),
                            sources=d.get("sources", []), rules_text=d.get("rules_text", ""),
                            hashtags=d.get("hashtags", []), status="joined",
                            fetched_at=time.time()))
    return out


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(prog="clipper.whop",
                                 description="Whop Content Rewards clipping agent")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("discover", help="list suitable live campaigns")
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--enrich", type=int, default=8)
    p.add_argument("--all", action="store_true", help="show unsuitable too")

    p = sub.add_parser("show", help="campaign details")
    p.add_argument("ref", help="URL, id, or discover-list number")

    p = sub.add_parser("add", help="track a campaign")
    p.add_argument("url")
    p.add_argument("--source", action="append", default=[],
                   help="footage URL (repeatable)")
    p.add_argument("--status", default="joined")

    p = sub.add_parser("source", help="add footage sources to a campaign")
    p.add_argument("ref")
    p.add_argument("urls", nargs="+")

    p = sub.add_parser("rules", help="save full rules text (from inside Whop)")
    p.add_argument("ref")
    p.add_argument("text", nargs="+")

    p = sub.add_parser("do", help="fulfill: produce compliant clips")
    p.add_argument("ref")
    p.add_argument("--count", type=int, default=None)
    p.add_argument("--source", action="append", default=[])

    p = sub.add_parser("posted", help="mark a clip posted/submitted")
    p.add_argument("clip_id")
    p.add_argument("post_url", nargs="?")
    p.add_argument("--submitted", action="store_true")

    sub.add_parser("list", help="tracked campaigns + progress")
    args = ap.parse_args()

    prefs = WhopPrefs.from_env()
    state = load_state(prefs.state_file)

    if args.cmd == "discover":
        print("[whop] fetching Content Rewards marketplace...", flush=True)
        cards = discover(args.limit, args.enrich)
        for c in cards:
            upsert_campaign(state, c)
        for c in load_curated(os.environ.get("WHOP_CAMPAIGNS_FILE", "")):
            upsert_campaign(state, c)
        good = suitable(cards, prefs)
        state["last_discover"] = [c.id for c in (good if not args.all else cards)]
        save_state(state, prefs.state_file)
        show = good if not args.all else cards
        print(f"[whop] {len(good)}/{len(cards)} suitable "
              f"(min ${prefs.min_rate}/1k, ${prefs.min_budget_left:,.0f} left)\n")
        for i, c in enumerate(show, 1):
            print(campaign_card(c, i) + "\n")
        if not show:
            print("No suitable campaigns. Loosen WHOP_MIN_RATE / WHOP_MIN_BUDGET_LEFT.")

    elif args.cmd == "show":
        cid = resolve_ref(state, args.ref)
        c = get_campaign(state, cid) if cid else None
        if c and not c.title and _UUID_RE.search(args.ref):
            pass
        if args.ref.startswith("http") and (not c or not c.title):
            c = fetch_campaign(args.ref)
            upsert_campaign(state, c)
            save_state(state, prefs.state_file)
        if not c:
            raise SystemExit(f"unknown campaign: {args.ref}")
        print(campaign_card(c))
        if c.description:
            print(f"\n{c.description}")
        rules = parse_rules(f"{c.description}\n{c.rules_text}")
        if rules["hashtags"] or rules["mentions"]:
            print(f"\n#️⃣ {' '.join(rules['hashtags'] + rules['mentions'])}")
        if rules["min_len"] or rules["max_len"]:
            print(f"⏱️ length: {rules['min_len'] or '?'}–{rules['max_len'] or '?'}s")
        for b in rules["banned"]:
            print(f"⚠️ {b}")
        if c.reference_links:
            print("\n📎 Reference materials:")
            for r in c.reference_links:
                print(f"  • {r['label']}: {r['url']}")
        if c.sources:
            print("\n🎞️ Sources:")
            for s in c.sources:
                print(f"  • {s}")
        if c.join_url:
            print(f"\n➡️ Join/submit: {c.join_url}")

    elif args.cmd == "add":
        c = fetch_campaign(args.url)
        c.status = args.status
        c.sources = args.source
        upsert_campaign(state, c)
        save_state(state, prefs.state_file)
        print(f"tracking {c.title or c.id} [{c.status}] ({len(c.sources)} source(s))")

    elif args.cmd == "source":
        cid = resolve_ref(state, args.ref)
        c = get_campaign(state, cid) if cid else None
        if not c:
            raise SystemExit(f"unknown campaign: {args.ref}")
        c.sources.extend(u for u in args.urls if u not in c.sources)
        upsert_campaign(state, c)
        save_state(state, prefs.state_file)
        print(f"{c.title or cid}: {len(c.sources)} source(s)")

    elif args.cmd == "rules":
        cid = resolve_ref(state, args.ref)
        c = get_campaign(state, cid) if cid else None
        if not c:
            raise SystemExit(f"unknown campaign: {args.ref}")
        c.rules_text = " ".join(args.text)
        r = parse_rules(c.rules_text)
        c.hashtags = sorted(set(c.hashtags + r["hashtags"]))
        upsert_campaign(state, c)
        save_state(state, prefs.state_file)
        print(f"rules saved ({len(c.rules_text)} chars, "
              f"{len(r['hashtags'])} hashtags, {len(r['banned'])} warnings)")

    elif args.cmd == "do":
        cid = resolve_ref(state, args.ref)
        if not cid:
            raise SystemExit(f"unknown campaign: {args.ref}")
        res = fulfill(cid, prefs, count=args.count, sources=args.source or None)
        print(f"\n✅ {len(res['clips'])} clip(s) ready in "
              f"{os.path.dirname(res['clips'][0]['path']) if res['clips'] else '?'}\n")
        print(res["checklist"])

    elif args.cmd == "posted":
        found = None
        for cid, d in state["campaigns"].items():
            for clip in d.get("clips", []):
                if clip.get("clip_id") == args.clip_id:
                    found = (cid, clip)
        if not found:
            raise SystemExit(f"unknown clip: {args.clip_id}")
        cid, clip = found
        if args.post_url:
            clip["post_url"] = args.post_url
            clip["status"] = "posted"
        if args.submitted:
            clip["status"] = "submitted"
        save_state(state, prefs.state_file)
        c = get_campaign(state, cid)
        print(f"{args.clip_id} -> {clip['status']} "
              f"({c.title if c else cid}) {clip.get('post_url', '')}")

    elif args.cmd == "list":
        if not state["campaigns"]:
            print("No tracked campaigns. Run: python -m clipper.whop discover")
            return
        for cid, d in state["campaigns"].items():
            clips = d.get("clips", [])
            n_post = sum(1 for x in clips if x.get("status") in ("posted", "submitted"))
            print(f"• {d.get('title') or cid} [{d.get('status')}] "
                  f"${d.get('rate_per_1k', 0)}/1k · {len(d.get('sources', []))} sources · "
                  f"{len(clips)} clips ({n_post} posted)")


if __name__ == "__main__":
    main()
