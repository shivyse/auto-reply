"""Lightweight tests for the clipping automation (no network, no heavy deps).

Run:  python -m pytest tests/ -q   (or: python tests/test_clipper.py)
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from clipper.captions import build_ass, chunk_words
from clipper.config import ClipperConfig
from clipper.moments import Moment, _finalize, _heuristic_moments
from clipper.transcriber import Segment, Word, load_transcript, save_transcript, vtt_to_segments
from clipper import watcher


def _seg(start, text, wps=2.5):
    toks = text.split()
    dur = len(toks) / wps
    words, t = [], start
    for tok in toks:
        d = dur / max(len(toks), 1)
        words.append(Word(t, t + d, tok))
        t += d
    return Segment(start, start + dur, text, words)


class TestConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = ClipperConfig.from_env()
        self.assertEqual(cfg.style, "crop")
        self.assertGreater(cfg.max_len, cfg.min_len)

    def test_env_override(self):
        with mock.patch.dict(os.environ, {"CLIP_COUNT": "5", "CLIP_STYLE": "blur"}):
            cfg = ClipperConfig.from_env()
            self.assertEqual(cfg.clip_count, 5)
            self.assertEqual(cfg.style, "blur")


class TestVTT(unittest.TestCase):
    SAMPLE = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello world this is a test

00:00:05.500 --> 00:00:07.000
Nobody talks about this <b>secret</b>!
"""

    def test_parse(self):
        with tempfile.NamedTemporaryFile("w", suffix=".vtt", delete=False) as f:
            f.write(self.SAMPLE)
            path = f.name
        try:
            segs = vtt_to_segments(path)
        finally:
            os.remove(path)
        self.assertEqual(len(segs), 2)
        self.assertAlmostEqual(segs[0].start, 1.0)
        self.assertAlmostEqual(segs[0].end, 3.0)
        self.assertEqual(segs[0].text, "Hello world this is a test")
        self.assertEqual(len(segs[0].words), 6)
        # word timings span the cue and are ordered
        self.assertAlmostEqual(segs[0].words[0].start, 1.0)
        self.assertAlmostEqual(segs[0].words[-1].end, 3.0)
        # html tags stripped
        self.assertNotIn("<b>", segs[1].text)


class TestTranscriptIO(unittest.TestCase):
    def test_roundtrip(self):
        segs = [_seg(0.0, "Hello world."), _seg(2.0, "Second line here.")]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_transcript(segs, path)
            back = load_transcript(path)
        finally:
            os.remove(path)
        self.assertEqual(len(back), 2)
        self.assertEqual(back[0].text, "Hello world.")
        self.assertEqual(len(back[0].words), 2)
        self.assertAlmostEqual(back[1].words[0].start, 2.0)


class TestMoments(unittest.TestCase):
    def _transcript(self):
        lines = [
            (0, "Welcome back to the show everyone, today we talk about routines."),
            (8, "First, I wake up early and drink some water every single morning."),
            (16, "Nobody talks about this secret! Stop doing cardio every day, it is a huge mistake."),
            (26, "Instead, here is why walking actually burns more fat for beginners like you."),
            (36, "Second topic: I bought new shoes last week and they are very comfortable."),
            (46, "The weather has been nice and I enjoy reading books on the balcony."),
            (56, "What if I told you the truth about money? This one trick changed everything!"),
            (66, "Believe it or not, I quit my job after this shocking discovery about savings."),
            (76, "Thanks for watching, subscribe for more videos next week everyone."),
        ]
        return [_seg(t, text) for t, text in lines]

    def test_heuristic_picks_hooks(self):
        moms = _heuristic_moments(self._transcript(), 90.0, count=2,
                                  min_len=10, max_len=30)
        self.assertEqual(len(moms), 2)
        for m in moms:
            self.assertGreaterEqual(m.end - m.start, 10)
            self.assertLessEqual(m.end - m.start, 30)
            self.assertTrue(m.title)
            self.assertTrue(m.hashtags)
        # top pick should be one of the hooky regions (16-36s or 56-76s)
        top = moms[0]
        hooky = (15 <= top.start <= 37) or (55 <= top.start <= 77)
        self.assertTrue(hooky, f"top pick starts at {top.start}, expected a hook region")

    def test_finalize_clamps_and_dedupes(self):
        raw = [
            {"start": 5, "end": 8, "title": "short one", "score": 90},   # too short -> extended
            {"start": 6, "end": 40, "title": "overlap", "score": 10},    # overlaps -> dropped
            {"start": 50, "end": 500, "title": "too long", "score": 80},  # too long -> trimmed
        ]
        moms = _finalize(raw, 100.0, 20.0, 30.0, 3)
        self.assertEqual(len(moms), 2)
        self.assertGreaterEqual(moms[0].end - moms[0].start, 20)
        self.assertLessEqual(moms[1].end - moms[1].start, 30)

    def test_overlap_helper(self):
        a = Moment(0, 10)
        b = Moment(5, 15)
        from clipper.moments import _overlap
        self.assertEqual(_overlap(a, b), 5)

    def test_llm_path_with_mocked_api(self):
        from clipper import moments as M
        body = json.dumps({"choices": [{"message": {"content": """```json
[{"start": 13.0, "end": 30.0, "title": "Stop doing cardio",
"hook": "Nobody talks about this secret",
"hashtags": ["#fitness", "#shorts"], "reason": "strong hook", "score": 95}]
```"""}}]}).encode()

        class R:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return body

        with mock.patch.object(M.urllib.request, "urlopen", return_value=R()):
            moms = M.pick_moments(self._transcript(), 90.0, count=1,
                                  min_len=10, max_len=30,
                                  use_llm=True, api_key="fake-key")
        self.assertEqual(len(moms), 1)
        self.assertEqual(moms[0].title, "Stop doing cardio")
        self.assertIn("#fitness", moms[0].hashtags)
        self.assertGreaterEqual(moms[0].end - moms[0].start, 10)

    def test_llm_failure_falls_back_to_heuristic(self):
        from clipper import moments as M
        with mock.patch.object(M.urllib.request, "urlopen",
                               side_effect=Exception("no network")):
            moms = M.pick_moments(self._transcript(), 90.0, count=1,
                                  min_len=10, max_len=30,
                                  use_llm=True, api_key="fake-key")
        self.assertEqual(len(moms), 1)
        self.assertIn("heuristic", moms[0].reason)


class TestCaptions(unittest.TestCase):
    def test_ass_events(self):
        words = [Word(i * 0.4, i * 0.4 + 0.35, w)
                 for i, w in enumerate("nobody talks about this secret".split())]
        with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as f:
            path = f.name
        try:
            build_ass(words, 0.0, 3.0, path)
            content = open(path, encoding="utf-8").read()
        finally:
            os.remove(path)
        self.assertIn("[V4+ Styles]", content)
        self.assertIn("Dialogue:", content)
        self.assertIn("SECRET", content)  # uppercased active word
        self.assertIn("\\1c", content)     # highlight override present

    def test_chunking(self):
        words = [Word(i, i + 0.5, f"w{i}") for i in range(10)]
        chunks = chunk_words(words)
        self.assertTrue(all(len(c) <= 4 for c in chunks))

    def test_empty_words_ok(self):
        with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as f:
            path = f.name
        try:
            build_ass([], 0.0, 5.0, path)
            content = open(path, encoding="utf-8").read()
        finally:
            os.remove(path)
        self.assertIn("[Events]", content)


class TestWatcher(unittest.TestCase):
    FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns="http://www.w3.org/2005/Atom">
  <entry><id>yt:video:AAA111</id><title>First</title>
    <link href="https://www.youtube.com/watch?v=AAA111"/>
    <published>2026-01-01T00:00:00+00:00</published></entry>
  <entry><id>yt:video:BBB222</id><title>Second</title>
    <link href="https://www.youtube.com/watch?v=BBB222"/>
    <published>2026-01-02T00:00:00+00:00</published></entry>
</feed>"""

    def _fake_urlopen(self, *a, **k):
        class R:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return TestWatcher.FEED.encode()
        return R()

    def test_fetch_parses_feed(self):
        with mock.patch.object(watcher.urllib.request, "urlopen", self._fake_urlopen):
            vids = watcher.fetch_channel_videos("UCxxxxxxxxxxxxxxxxxxxxxx")
        self.assertEqual(len(vids), 2)
        self.assertEqual(vids[0].id, "AAA111")
        self.assertIn("watch?v=AAA111", vids[0].url)

    def test_poll_tracks_seen(self):
        with tempfile.TemporaryDirectory() as d:
            state = os.path.join(d, "state.json")
            with mock.patch.object(watcher.urllib.request, "urlopen", self._fake_urlopen):
                first = watcher.poll_once(["UCxxxxxxxxxxxxxxxxxxxxxx"], state)
                self.assertEqual(first, [])  # first run: baseline, no backlog spam
                self.assertTrue(os.path.exists(state))
                saved = json.load(open(state))
                self.assertIn("AAA111", saved["UCxxxxxxxxxxxxxxxxxxxxxx"]["seen"])

    def test_resolve_passthrough(self):
        self.assertEqual(watcher.resolve_channel_id("UCxxxxxxxxxxxxxxxxxxxxxx"),
                         "UCxxxxxxxxxxxxxxxxxxxxxx")
        self.assertEqual(
            watcher.resolve_channel_id("https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxx"),
            "UCxxxxxxxxxxxxxxxxxxxxxx")


if __name__ == "__main__":
    unittest.main(verbosity=2)
