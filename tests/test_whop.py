"""Tests for the Whop Content Rewards integration (no network).

Run:  python tests/test_whop.py
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from clipper import whop
from clipper.whop import (Campaign, WhopPrefs, parse_campaign_html,
                          parse_discover_html, parse_money, parse_rules,
                          score_campaign, load_state, save_state,
                          upsert_campaign, resolve_ref)

DISCOVER_HTML = """
<html><body>
<div class="card">
<a href="/discover/24ad920b-d24f-479e-9cef-f22182e4a0c0">View Campaign</a>
<h2>Call of Duty - MW4 Beta Gameplay Clipping</h2>
<p>Post gameplay to TikTok, Instagram Reels, and YouTube Shorts.</p>
<span>$39k/$105k</span><span>489 joined</span><span>$1.75/1K</span>
</div>
<div class="card">
<a href="/discover/188c3e39-7850-4896-94df-e7a5be0cfec3">View Campaign</a>
<h2>Boxabl Official Clipping</h2>
<p>Clip the best moments from pre-approved videos.</p>
<span>$16k/$85k</span><span>729 joined</span><span>$0.50/1K</span>
</div>
</body></html>
"""

DETAIL_HTML = """
<html><head><title>Call of Duty - Modern Warfare 4 Beta Clipping by Clipping Culture | Content Rewards</title></head>
<body>
<h1>Call of Duty - Modern Warfare 4 Beta Clipping</h1>
<div>Creators489</div><div>$1.75/1K</div>
<a href="https://whop.com/experiences/exp_zeADOv9rOOKk2x/campaigns/24ad920b-d24f-479e-9cef-f22182e4a0c0">Join Campaign</a>
<div>$39.5K/$105K38% used</div>
<p>Post Modern Warfare 4 Multiplayer Beta gameplay to TikTok, Instagram Reels, and YouTube Shorts. Edit the source footage into polished clips, do not post it as a raw reel.</p>
<div>TikTok$1.75 per 1k views $3.50 min$2.5K max</div>
<div>Instagram$1.50 per 1k views $4.50 min$2.5K max</div>
<div>YouTube$1.75 per 1k views $5.25 min$2.5K max</div>
<h2>Reference materials</h2>
<a href="https://docs.google.com/document/d/1AaBbb/edit">Footage guide</a>
<a href="https://drive.google.com/drive/folders/xyz">Source clips drive</a>
</body></html>
"""


class TestMoney(unittest.TestCase):
    def test_parse_money(self):
        self.assertEqual(parse_money("$39.5K"), 39500)
        self.assertEqual(parse_money("$105K"), 105000)
        self.assertEqual(parse_money("$3.50"), 3.5)
        self.assertEqual(parse_money("$2.5K"), 2500)
        self.assertEqual(parse_money("$220k"), 220000)


class TestDiscover(unittest.TestCase):
    def test_parse_cards(self):
        cards = parse_discover_html(DISCOVER_HTML)
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0].id, "24ad920b-d24f-479e-9cef-f22182e4a0c0")
        self.assertAlmostEqual(cards[0].rate_per_1k, 1.75)
        self.assertEqual(cards[0].budget_spent, 39000)
        self.assertEqual(cards[0].budget_total, 105000)
        self.assertEqual(cards[0].creators, 489)
        self.assertIn("/discover/", cards[0].url)
        self.assertAlmostEqual(cards[1].rate_per_1k, 0.50)


class TestDetail(unittest.TestCase):
    def test_parse_detail(self):
        c = parse_campaign_html(
            DETAIL_HTML,
            "https://contentrewards.com/discover/24ad920b-d24f-479e-9cef-f22182e4a0c0")
        self.assertEqual(c.id, "24ad920b-d24f-479e-9cef-f22182e4a0c0")
        self.assertIn("Modern Warfare", c.title)
        self.assertAlmostEqual(c.rate_per_1k, 1.75)
        self.assertEqual(c.budget_total, 105000)
        self.assertEqual(c.creators, 489)
        self.assertIn("whop.com/experiences", c.join_url)
        # per-platform payouts
        plats = {p.platform: p for p in c.payouts}
        self.assertAlmostEqual(plats["tiktok"].rate_per_1k, 1.75)
        self.assertEqual(plats["tiktok"].max_payout, 2500)
        self.assertAlmostEqual(plats["instagram"].rate_per_1k, 1.50)
        # references
        urls = [r["url"] for r in c.reference_links]
        self.assertTrue(any("docs.google.com" in u for u in urls))
        self.assertTrue(any("drive.google.com" in u for u in urls))
        # derived
        self.assertAlmostEqual(c.budget_left, 105000 - 39500)
        self.assertGreater(c.pct_used, 30)


class TestRules(unittest.TestCase):
    TEXT = ("Post to TikTok and YouTube Shorts. Use #mw4 #callofduty and tag @clipculture. "
            "Clips must be at least 15 seconds and under 60 seconds. "
            "Do not post raw footage without editing. Never add your own watermark.")

    def test_parse(self):
        r = parse_rules(self.TEXT)
        self.assertIn("#mw4", r["hashtags"])
        self.assertIn("@clipculture", r["mentions"])
        self.assertEqual(r["min_len"], 15)
        self.assertEqual(r["max_len"], 60)
        self.assertIn("tiktok", r["platforms"])
        self.assertIn("youtube", r["platforms"])
        self.assertEqual(len(r["banned"]), 2)


class TestScoring(unittest.TestCase):
    def test_suitable_sorted(self):
        good = Campaign(id="a" * 36, title="Gaming clips", rate_per_1k=2.0,
                        budget_total=50000, budget_spent=5000,
                        payouts=[whop.Payout("tiktok", 2.0, 5, 1000)])
        poor = Campaign(id="b" * 36, title="Low pay", rate_per_1k=0.2,
                        budget_total=50000, budget_spent=1000)
        dry = Campaign(id="c" * 36, title="Dry pool", rate_per_1k=3.0,
                       budget_total=10000, budget_spent=9900)
        prefs = WhopPrefs(min_rate=0.5, min_budget_left=1000, max_used_pct=95)
        ranked = whop.suitable([poor, dry, good], prefs)
        self.assertEqual([c.id for c in ranked], ["a" * 36])
        self.assertGreater(good.score, 0)

    def test_exclude_and_platform_filters(self):
        c = Campaign(id="d" * 36, title="Casino slots clipping", rate_per_1k=5.0,
                     budget_total=100000, budget_spent=1000,
                     payouts=[whop.Payout("x", 5.0)])
        prefs = WhopPrefs(exclude=["casino"], platforms=["tiktok"])
        score_campaign(c, prefs)
        self.assertEqual(c.score, 0.0)
        c2 = Campaign(id="e" * 36, title="Fitness clips", rate_per_1k=1.0,
                      budget_total=100000, budget_spent=1000,
                      payouts=[whop.Payout("tiktok", 1.0)])
        score_campaign(c2, prefs)
        self.assertGreater(c2.score, 0.0)


class TestState(unittest.TestCase):
    def test_roundtrip_and_resolve(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "w.json")
            state = load_state(path)
            c = Campaign(id="24ad920b-d24f-479e-9cef-f22182e4a0c0",
                         title="MW4", status="joined", sources=["https://youtu.be/x"])
            upsert_campaign(state, c)
            state["last_discover"] = [c.id]
            save_state(state, path)
            back = load_state(path)
            self.assertEqual(back["campaigns"][c.id]["title"], "MW4")
            # upsert preserves user fields when re-discovered
            lite = Campaign(id=c.id, title="", rate_per_1k=1.75)
            upsert_campaign(back, lite)
            self.assertEqual(back["campaigns"][c.id]["sources"], ["https://youtu.be/x"])
            self.assertEqual(back["campaigns"][c.id]["status"], "joined")
            self.assertEqual(resolve_ref(back, "1"), c.id)
            self.assertEqual(resolve_ref(back, c.id[:8]), c.id)
            self.assertEqual(resolve_ref(back, c.url or f"/discover/{c.id}"), c.id)


class TestFulfill(unittest.TestCase):
    def test_fulfill_maps_campaign_to_jobs(self):
        with tempfile.TemporaryDirectory() as d:
            prefs = WhopPrefs(state_file=os.path.join(d, "w.json"))
            state = load_state(prefs.state_file)
            c = Campaign(
                id="f" * 36, title="Test Campaign", status="joined",
                rate_per_1k=1.5, budget_total=50000, budget_spent=5000,
                join_url="https://whop.com/experiences/exp_x/campaigns/" + "f" * 36,
                sources=["https://example.com/video"],
                rules_text="Use #testclip and tag @brand. At least 10 seconds.",
                payouts=[whop.Payout("tiktok", 1.5, 3, 500)])
            upsert_campaign(state, c)
            save_state(state, prefs.state_file)

            calls = []

            def fake_run_job(url=None, file_path=None, cfg=None, count=None, **kw):
                calls.append({"url": url, "count": count,
                              "min": cfg.min_len, "max": cfg.max_len,
                              "out": cfg.output_dir})
                return {"clips": [
                    {"path": f"/tmp/{i}.mp4", "title": f"Clip {i}",
                     "hook": "hook", "hashtags": ["#shorts"],
                     "start": 0, "end": 12, "score": 9, "reason": "t"}
                    for i in range(count or 1)]}

            from clipper.config import ClipperConfig
            cfg = ClipperConfig(output_dir=d, min_len=20, max_len=55)
            with mock.patch.dict(os.environ, {"WHOP_AUTO_UPLOAD": ""}):
                res = whop.fulfill("f" * 36, prefs, count=2,
                                   run_job_fn=fake_run_job, cfg=cfg)

            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["url"], "https://example.com/video")
            self.assertEqual(calls[0]["count"], 2)
            self.assertEqual(calls[0]["min"], 10)  # from rules text
            self.assertIn("whop_ffffffff", calls[0]["out"])
            self.assertEqual(len(res["clips"]), 2)
            self.assertIn("#testclip", res["clips"][0]["hashtags"])
            self.assertIn("whop.com/experiences", res["checklist"])
            self.assertIn("#testclip", res["checklist"])
            # state updated
            back = load_state(prefs.state_file)
            self.assertEqual(len(back["campaigns"]["f" * 36]["clips"]), 2)

    def test_fulfill_needs_sources(self):
        with tempfile.TemporaryDirectory() as d:
            prefs = WhopPrefs(state_file=os.path.join(d, "w.json"))
            state = load_state(prefs.state_file)
            upsert_campaign(state, Campaign(id="e" * 36, title="No sources"))
            save_state(state, prefs.state_file)
            with self.assertRaises(ValueError) as ctx:
                whop.fulfill("e" * 36, prefs, run_job_fn=lambda **k: None)
            self.assertIn("/whop source", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
