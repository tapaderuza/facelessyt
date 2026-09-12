"""Small evidence gate for structured proposals, not a natural-language truth judge.

Snapshot and produced-topic registry must be supplied by the host, never the model.
Passing yields ready_for_review, never permission to upload or publish.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone


def verify(proposal: dict, snapshot: dict, produced: set[str], *, now: datetime) -> dict:
    reasons: list[str] = []
    if not isinstance(proposal, dict):
        return {'status': 'blocked', 'reasons': ['invalid_proposal']}
    if now.tzinfo is None:
        raise ValueError('now must include a timezone')
    try:
        generated = datetime.fromisoformat(snapshot['generated_at'])
        if generated.tzinfo is None:
            raise ValueError('missing timezone')
        age = now - generated
        if age < timedelta(0) or age > timedelta(days=21):
            reasons.append('snapshot_outside_window')
    except (KeyError, ValueError, TypeError):
        reasons.append('invalid_snapshot_date')

    topic = proposal.get('topic_key')
    if not isinstance(topic, str) or not topic.strip():
        reasons.append('missing_topic_key')
    elif topic.strip().casefold() in {key.strip().casefold() for key in produced}:
        reasons.append('already_produced')

    # Do not silently accept proposal fields that this small verifier does not check.
    expected = {'topic_key', 'evidence_url', 'claimed_score', 'forecast_views'}
    if set(proposal) - expected:
        reasons.append('unexpected_fields')
    if proposal.get('forecast_views') is not None:
        reasons.append('unsupported_forecast')
    evidence_url = proposal.get('evidence_url')
    matches = [row for row in snapshot.get('outliers', [])
               if isinstance(row, dict) and row.get('url') == evidence_url]
    actual = None
    if not isinstance(evidence_url, str) or len(matches) != 1:
        reasons.append('evidence_not_unique_in_snapshot')
    else:
        row = matches[0]
        views, baseline = row.get('views'), row.get('channel_baseline')
        if (type(views) is not int or views < 0 or type(baseline) is not int or baseline <= 0):
            reasons.append('invalid_source_numbers')
        else:
            actual = round(views / baseline, 2)
            score = proposal.get('claimed_score')
            if type(score) not in (int, float) or not math.isfinite(score) or abs(score - actual) > 0.011:
                reasons.append('score_mismatch')
            if actual < 3:
                reasons.append('below_evidence_threshold')
    return {'status': 'blocked' if reasons else 'ready_for_review',
            'reasons': reasons, 'recomputed_score': actual,
            'scope': 'Structured fields only; semantic fit and editorial quality need human review.'}


def replay(snapshot: dict) -> dict:
    """Deliberately injected fixtures. NOT sampled model responses or live analytics."""
    row = snapshot['outliers'][0]
    valid = {'topic_key': 'proof-gate', 'evidence_url': row['url'],
             'claimed_score': round(row['views'] / row['channel_baseline'], 2),
             'forecast_views': None}
    at = datetime(2026, 9, 12, tzinfo=timezone.utc)
    produced = {'outlier-miner', 'topic-watch'}
    cases = [
        ('valid', valid, at, 'ready_for_review'),
        ('wrong_score', {**valid, 'claimed_score': 99.0}, at, 'blocked'),
        ('missing_source', {**valid, 'evidence_url': 'https://example.invalid/missing'}, at, 'blocked'),
        ('duplicate_topic', {**valid, 'topic_key': 'outlier-miner'}, at, 'blocked'),
        ('future_views', {**valid, 'forecast_views': 100000}, at, 'blocked'),
        ('old_snapshot', valid, at + timedelta(days=30), 'blocked'),
        # Deliberate blind spot: different spelling for effectively the same idea.
        ('semantic_duplicate', {**valid, 'topic_key': 'youtube-topic-finder'}, at, 'ready_for_review'),
    ]
    results = []
    for name, proposal, now, expected in cases:
        verdict = verify(proposal, snapshot, produced, now=now)
        results.append({'case': name, 'kind': 'injected_fixture', 'proposal': proposal,
                        'expected': expected, 'verdict': verdict,
                        'matches_expectation': verdict['status'] == expected})
    return {'kind': 'offline_fault_injection', 'clock': at.isoformat(),
            'snapshot_date': snapshot['generated_at'], 'source_count': len(snapshot['outliers']),
            'source_numbers': {'views': row['views'], 'baseline': row['channel_baseline']},
            'cases': results,
            'note': 'No model accuracy measured. Semantic duplicate intentionally passes for human review.'}
