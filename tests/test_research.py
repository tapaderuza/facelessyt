import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

from facelessyt.opportunities import counts, latest_snapshot, rank, size_band
from facelessyt.memory_budget import Budget, GIB, calculate, demo
from facelessyt.visual_research import ocr_words, validate_thumbnail_url, video_id
from facelessyt.miner import mine
from facelessyt.youtube import Channel, Video, Client

NOW = datetime(2026, 9, 12, tzinfo=timezone.utc)


def row(channel="A", subs=50_000, score=4, title="Local AI", url=None):
    return dict(channel_title=channel, channel_subs=subs, score=score,
                age_days=10, title=title, url=url or f"https://youtube.com/watch?v={channel}")


def snapshot(rows):
    return dict(niche="test", generated_at=NOW.isoformat(), outliers=rows)


class OpportunityTests(unittest.TestCase):
    def test_bands_and_unknown(self):
        self.assertEqual([size_band(n) for n in [0, 9999, 10000, 100000, 100001, 250000, 250001, None, -1, True, float('nan')]],
                         ["micro", "micro", "small", "small", "mid", "mid", "large", "unknown", "unknown", "unknown", "unknown"])

    def test_counts_dedupe_and_unknown(self):
        a = row()
        report = counts([a, a, row("A", url="second"), row("B", None)])
        self.assertEqual(report["channels"], 2)
        self.assertEqual(report["bands"]["small"], 1)
        self.assertEqual(report["bands"]["unknown"], 1)

    def test_conflicting_size_is_unknown(self):
        self.assertEqual(counts([row(), row(subs=500000, url="other")])["bands"]["unknown"], 1)

    def test_id_dedupes_channel_rename(self):
        a, b = row(), row("RENAMED", url="other")
        a["channel_id"] = b["channel_id"] = "UC1"
        self.assertEqual(counts([a, b])["channels"], 1)

    def test_channel_balanced_score(self):
        rows = [row("A", score=10, url=str(i)) for i in range(9)] + [row("B", score=4)]
        result = rank(snapshot(rows), {"episodes": []}, now=NOW)
        self.assertEqual(result["candidates"][0]["channel_balanced_median_score"], 7)
        self.assertEqual(result["selected"], "local-memory-budget")
        self.assertEqual(result["scope"], "outliers_only")
        self.assertIsNone(result["market_saturation"])

    def test_catalog_alias_blocks(self):
        catalog = {"episodes": [{"topic_key": "other", "aliases": ["local-memory-budget"]}]}
        self.assertIsNone(rank(snapshot([row(), row("B")]), catalog, now=NOW)["selected"])

    def test_large_and_unknown_do_not_validate(self):
        result = rank(snapshot([row(subs=None), row("B", 900000)]), {"episodes": []}, now=NOW)
        self.assertIsNone(result["selected"])

    def test_full_sample_uses_nonoutliers_for_competition(self):
        data = snapshot([row(), row("B")])
        data["coverage"] = {"scope": "seed_channel_sample", "videos": data["outliers"] + [row("C", 500000, 1)]}
        c = rank(data, {"episodes": []}, now=NOW)["candidates"][0]
        self.assertEqual(c["observed_competition"]["channels"], 3)
        self.assertEqual(c["outlier_channel_counts"]["channels"], 2)

    def test_stale_and_future(self):
        data = snapshot([row(), row("B")])
        self.assertIsNone(rank(data, {"episodes": []}, now=NOW + timedelta(days=22))["selected"])
        with self.assertRaises(ValueError):
            rank(data, {"episodes": []}, now=NOW - timedelta(days=1))

    def test_density_denominator_is_sample_not_market(self):
        data = snapshot([row(), row("B")])
        data["coverage"] = {"scope": "seed_channel_sample", "videos": data["outliers"],
                            "channels": [row(), row("B"), row("C"), row("D")]}
        result = rank(data, {"episodes": []}, now=NOW)
        competition = result["candidates"][0]["observed_competition"]
        self.assertEqual(competition["topic_share_within_sample_by_band"]["small"], .5)
        self.assertIsNone(competition["topic_share_within_sample_by_band"]["large"])
        self.assertIsNone(result["market_saturation"])

    def test_bad_score(self):
        with self.assertRaises(ValueError):
            rank(snapshot([row(score=float('nan'))]), {"episodes": []}, now=NOW)

    def test_latest_uses_timestamp_not_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old, new = snapshot([]), snapshot([])
            old["generated_at"] = "2026-09-10T00:00:00+00:00"
            (root / "outliers-test-z.json").write_text(json.dumps(old))
            (root / "outliers-test-a.json").write_text(json.dumps(new))
            self.assertEqual(latest_snapshot(root, "test").name, "outliers-test-a.json")

    def test_empty_does_not_invent_topic(self):
        self.assertIsNone(rank(snapshot([]), {"episodes": []}, now=NOW)["selected"])


class PipelineTests(unittest.TestCase):
    def test_mine_preserves_nonoutliers(self):
        client = Mock()
        channel = Channel("UC1", "A", "@a", 100, 10, "UU1")
        client.resolve_channel.return_value = channel
        client.videos.return_value = [Video(str(i), "Local AI", "UC1", "A",
            datetime.now(timezone.utc) - timedelta(days=20), 100, 0, 0, 600) for i in range(6)]
        coverage = {}
        found, warnings = mine(client, {"seed_channels": ["@a"]}, coverage=coverage)
        self.assertEqual(found, [])
        self.assertEqual(warnings, [])
        self.assertEqual(len(coverage["videos"]), 6)

    def test_api_picks_largest_available_thumbnail(self):
        client = Client("test")
        client._get = Mock(return_value={"items": [{"id": "x", "snippet": {
            "title": "X", "channelId": "C", "channelTitle": "C", "publishedAt": "2026-01-01T00:00:00Z",
            "thumbnails": {"small": {"width": 120, "height": 90, "url": "small"},
                           "high": {"width": 480, "height": 360, "url": "high"}}},
            "contentDetails": {"duration": "PT10M"}}]})
        self.assertEqual(client.videos(["x"])[0].thumbnail_url, "high")


class VisualPureTests(unittest.TestCase):
    def test_video_id_and_reject_other_hosts(self):
        self.assertEqual(video_id("https://www.youtube.com/watch?v=CpMCYO2oWBI"), "CpMCYO2oWBI")
        for url in ["https://evil.com/watch?v=CpMCYO2oWBI", "https://youtube.com/watch?v=../x", "file:///tmp/x"]:
            with self.assertRaises(ValueError):
                video_id(url)

    def test_thumbnail_rejects_ssrf_and_redirect_destinations(self):
        vid = "CpMCYO2oWBI"
        validate_thumbnail_url(f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg", vid)
        for url in ["http://127.0.0.1/a", f"https://i.ytimg.com.evil.com/vi/{vid}/x.jpg",
                    f"https://i.ytimg.com:8443/vi/{vid}/x.jpg", "https://i.ytimg.com/vi/other/hqdefault.jpg"]:
            with self.assertRaises(ValueError):
                validate_thumbnail_url(url, vid)

    def test_ocr_filters_confidence_not_fake_zero(self):
        data = {"text": ["", "AI", "Noise", "!!", "LOCAL"], "conf": [-1, 90, 12, 99, 50]}
        data.update({k: [1] * 5 for k in ["left", "top", "width", "height"]})
        self.assertEqual([w["text"] for w in ocr_words(data)], ["AI", "LOCAL"])


class MemoryTests(unittest.TestCase):
    def test_reproducible_four_cases(self):
        cases = demo()
        self.assertEqual(cases["short"]["total_budget_bytes"], 6 * GIB)
        self.assertEqual(cases["long"]["total_budget_bytes"], 9 * GIB)
        self.assertEqual(cases["long"]["headroom_bytes"], -GIB)
        self.assertEqual(cases["reduced_context"]["total_budget_bytes"], 7 * GIB)
        self.assertEqual(cases["two_sequences"]["total_budget_bytes"], 9 * GIB)
        self.assertEqual(cases["short"]["status"], "under_budget_not_verified")
        self.assertIsNone(cases["long"]["runtime_peak_bytes"])

    def test_reject_invalid_budget(self):
        for kwargs in [dict(tokens=-1), dict(sequences=0), dict(layers=True), dict(weight_bytes=1.5)]:
            with self.assertRaises(ValueError):
                calculate(Budget(**kwargs))


if __name__ == "__main__":
    unittest.main()
