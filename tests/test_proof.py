import copy
import math
import unittest
from datetime import datetime, timezone
from facelessyt.proof import verify


class ProofTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {'generated_at': '2026-09-10T00:00:00+00:00',
                         'outliers': [{'url': 'https://test.invalid/one', 'views': 120, 'channel_baseline': 10}]}
        self.proposal = {'topic_key': 'new', 'evidence_url': 'https://test.invalid/one',
                         'claimed_score': 12, 'forecast_views': None}
        self.now = datetime(2026, 9, 12, tzinfo=timezone.utc)

    def check(self, proposal=None, snapshot=None):
        return verify(self.proposal if proposal is None else proposal,
                      self.snapshot if snapshot is None else snapshot, {'old'}, now=self.now)

    def test_valid_goes_to_review_not_publication(self):
        self.assertEqual(self.check()['status'], 'ready_for_review')

    def test_bad_scores_and_types_fail_closed(self):
        for score in (math.nan, math.inf, True, '12', 99):
            with self.subTest(score=score):
                self.assertIn('score_mismatch', self.check({**self.proposal, 'claimed_score': score})['reasons'])

    def test_all_missing_evidence_is_rejected(self):
        self.assertIn('evidence_not_unique_in_snapshot', self.check({**self.proposal, 'evidence_url': 'other'})['reasons'])

    def test_duplicate_source_is_ambiguous(self):
        snap = copy.deepcopy(self.snapshot)
        snap['outliers'] *= 2
        self.assertEqual(self.check(snapshot=snap)['status'], 'blocked')

    def test_bad_baselines_do_not_crash(self):
        for baseline in (0, -1, None, True, '10'):
            snap = copy.deepcopy(self.snapshot)
            snap['outliers'][0]['channel_baseline'] = baseline
            self.assertIn('invalid_source_numbers', self.check(snapshot=snap)['reasons'])

    def test_time_boundary_is_inclusive(self):
        for stamp, blocked in [('2026-08-22T00:00:00+00:00', False),
                               ('2026-08-21T23:59:59+00:00', True),
                               ('2026-09-13T00:00:00+00:00', True), ('bad', True),
                               ('2026-09-10T00:00:00', True)]:
            with self.subTest(stamp=stamp):
                snap = {**self.snapshot, 'generated_at': stamp}
                self.assertEqual(self.check(snapshot=snap)['status'] == 'blocked', blocked)

    def test_duplicate_normalized_and_forecast_rejected(self):
        bad = {**self.proposal, 'topic_key': ' OLD ', 'forecast_views': 100000}
        self.assertEqual(set(self.check(bad)['reasons']), {'already_produced', 'unsupported_forecast'})

    def test_unchecked_extra_field_rejected(self):
        self.assertIn('unexpected_fields', self.check({**self.proposal, 'guarantee': 'viral'})['reasons'])

    def test_semantic_duplicate_is_explicit_blind_spot(self):
        # Different label is not proof of a different idea. Humans must review it.
        self.assertEqual(self.check({**self.proposal, 'topic_key': 'old-but-renamed'})['status'], 'ready_for_review')

    def test_missing_topic_and_non_object_rejected(self):
        self.assertEqual(self.check([])['status'], 'blocked')
        self.assertIn('missing_topic_key', self.check({**self.proposal, 'topic_key': ''})['reasons'])


if __name__ == '__main__':
    unittest.main()
