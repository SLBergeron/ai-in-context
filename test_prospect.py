import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import prospect
import schedule
from evaluate import evaluate


class ProspectTests(unittest.TestCase):
    def profile(self):
        return {"positioning_verified": True, "search_terms": ["founder"],
                "country": "US", "fit_keywords": ["founder"],
                "max_inactive_days": 120, "max_leads": 1}

    def test_feed_preserves_guest_and_public_contact_evidence(self):
        rss = b'''<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"><channel>
        <description>Founder conversations</description><link>https://example.org</link>
        <itunes:owner><itunes:email>host@example.org</itunes:email></itunes:owner>
        <item><title>Interview with Jane</title><pubDate>Thu, 08 Oct 2026 12:00:00 GMT</pubDate></item>
        </channel></rss>'''
        with patch.object(prospect, "fetch", return_value=rss):
            details = prospect.feed_details("https://example.org/feed")
        self.assertEqual(details["public_email"], "host@example.org")
        self.assertIn("Interview with Jane", details["guest_evidence"])
        self.assertEqual(details["latest_episode"], "2026-10-08T12:00:00+00:00")

    def test_unverified_positioning_prevents_scheduled_run(self):
        profile = self.profile()
        profile["positioning_verified"] = False
        with tempfile.TemporaryDirectory() as directory, patch.object(prospect, "fetch") as fetch:
            with self.assertRaisesRegex(ValueError, "unverified"):
                prospect.run(profile, Path(directory), Path(directory) / "state.json")
            fetch.assert_not_called()

    def test_repeat_runs_deliver_next_candidate_without_repeats(self):
        items = [{"collectionId": n, "collectionName": f"Founder {n}", "feedUrl": "https://example.org/feed"} for n in (1, 2)]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reports"
            state = Path(directory) / "state.json"
            with patch.object(prospect, "fetch", return_value=json.dumps({"results": items}).encode()), patch.object(prospect, "feed_details", side_effect=OSError("blocked")), patch.object(prospect.time, "sleep"):
                prospect.run(self.profile(), output, state)
                prospect.run(self.profile(), output, state)
                prospect.run(self.profile(), output, state)
            summaries = [json.loads(p.read_text()) for p in sorted(output.glob("*.json"))]
            self.assertEqual([s["new_delivered"] for s in summaries], [1, 1, 0])
            self.assertEqual(json.loads(state.read_text())["delivered"], ["1", "2"])
            self.assertEqual(summaries[0]["leads"][0]["public_email"], "")

    def test_all_discovery_failures_do_not_mark_delivered(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(prospect, "fetch", side_effect=OSError("denied")):
            state = Path(directory) / "state.json"
            with self.assertRaises(RuntimeError):
                prospect.run(self.profile(), Path(directory), state)
            self.assertFalse(state.exists())

    def test_csv_neutralizes_formula_cells(self):
        self.assertEqual(prospect.safe_cell("=1+1"), "'=1+1")

    def test_weekly_schedule_changes_only_at_monday_14_utc(self):
        self.assertEqual(schedule.cycle(schedule.ANCHOR), 0)
        self.assertEqual(schedule.cycle(schedule.ANCHOR + schedule.WEEK - 1), 0)
        self.assertEqual(schedule.cycle(schedule.ANCHOR + schedule.WEEK), 1)

    def test_eval_rejects_new_show_with_existing_publisher(self):
        previous = {'leads': [{'id': '1', 'show': 'First', 'host_or_publisher': 'Jane Smith'}]}
        report = {'leads': [{'id': '2', 'show': 'Second', 'host_or_publisher': 'JANE SMITH!'}]}
        result = evaluate(report, [previous], minimum_new=1)
        self.assertFalse(result['passed'])
        self.assertEqual(result['repeat_count'], 1)
        self.assertEqual(result['new_shows'], 1)
        self.assertEqual(result['new_host_or_publisher_proxies'], 0)

    def test_eval_checks_within_batch_and_prior_public_email(self):
        previous = {'leads': [{'id': '1', 'show': 'Old', 'public_email': 'host@example.org'}]}
        report = {'leads': [
            {'id': '2', 'show': 'Rename', 'host_or_publisher': 'New Name', 'public_email': 'HOST@example.org'},
            {'id': '3', 'show': 'New', 'host_or_publisher': 'Alice'},
            {'id': '4', 'show': 'Other', 'host_or_publisher': 'Alice'},
        ]}
        result = evaluate(report, [previous], minimum_new=1)
        self.assertEqual(result['repeat_count'], 2)
        self.assertEqual(result['new_host_or_publisher_proxies'], 1)
        self.assertFalse(result['passed'])

    def test_eval_pass_requires_yield_and_identity(self):
        self.assertFalse(evaluate({'leads': []}, [], minimum_new=1)['passed'])
        self.assertFalse(evaluate({'leads': [{'id': '1', 'show': 'Unknown'}]}, [], minimum_new=1)['passed'])
        self.assertTrue(evaluate({'leads': [{'id': '1', 'show': 'New', 'host_or_publisher': 'Alice'}]}, [], minimum_new=1)['passed'])

    def test_discovery_suppresses_existing_publisher_on_a_new_show(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'reports'
            output.mkdir()
            (output / 'prior.json').write_text(json.dumps({'run_at': '2020-01-01T00:00:00+00:00', 'leads': [{'id': '1', 'show': 'Old', 'host_or_publisher': 'Jane Smith'}]}))
            state = Path(directory) / 'state.json'
            state.write_text(json.dumps({'delivered': ['1']}))
            items = [{'collectionId': 2, 'collectionName': 'Founder New Show', 'artistName': 'JANE SMITH!', 'feedUrl': 'https://example.org/feed'}]
            with patch.object(prospect, 'fetch', return_value=json.dumps({'results': items}).encode()), patch.object(prospect, 'feed_details', side_effect=OSError('blocked')), patch.object(prospect.time, 'sleep'):
                prospect.run(self.profile(), output, state)
            self.assertEqual(json.loads(state.read_text())['delivered'], ['1'])
            result = json.loads(sorted(p for p in output.glob('*.json') if p.name != 'prior.json')[-1].read_text())
            self.assertEqual(result['blocked_repeats'], 1)
            self.assertEqual(result['new_delivered'], 0)


if __name__ == "__main__":
    unittest.main()
