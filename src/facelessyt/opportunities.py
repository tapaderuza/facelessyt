"""Auditable editorial screening, not a causal demand/CTR predictor."""
from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

from .clusters import assign, DEFAULT_CLUSTERS

# Explicit editorial policy for episode 4; not learned from view counts.
TOPICS = {
    "local models / self-hosting": ("local-memory-budget", "Executable memory-budget demo", None),
    "coding tools": ("coding-agent-fixes", "Executable before/after demo", None),
    "claude code workflows": ("claude-code-workflow", "Executable workflow demo", None),
    "comparisons": ("model-comparison", "Requires reproducible task benchmark", None),
    "agentic engineering / harnesses": ("proof-gate", "Executable harness", "Adjacent to episode 3; excluded for episode 4"),
    "building agents": ("outlier-miner", "Executable agent", "Adjacent to episodes 1 and 3; excluded for episode 4"),
    "just dropped / new release": (None, None, "Packaging pattern, not a coherent topic"),
    "courses / full guides": (None, None, "Format, not a coherent topic"),
}


def stamp(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Snapshot timestamps must have timezone")
    return dt


def latest_snapshot(directory: Path, niche: str) -> Path:
    if not niche or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in niche):
        raise ValueError("Invalid niche name")
    candidates = []
    for path in directory.glob(f"outliers-{niche}-*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("niche") == niche:
            candidates.append((stamp(data["generated_at"]), str(path), path))
    if not candidates:
        raise ValueError(f"No snapshots for {niche}")
    return max(candidates)[2]


def size_band(subs) -> str:
    if isinstance(subs, bool) or not isinstance(subs, (int, float)) or not math.isfinite(subs) or subs < 0:
        return "unknown"
    if subs < 10_000:
        return "micro"
    if subs <= 100_000:
        return "small"
    return "mid" if subs <= 250_000 else "large"


def unique_channels(rows: list[dict]) -> dict[str, list[dict]]:
    buckets, ids = defaultdict(list), defaultdict(set)
    for row in rows:
        if row.get("channel_id"):
            ids[row["channel_title"].casefold()].add(row["channel_id"])
    seen = set()
    for row in rows:
        if row["url"] in seen:
            continue
        seen.add(row["url"])
        title = row["channel_title"].casefold()
        matches = ids[title]
        key = row.get("channel_id") or (next(iter(matches)) if len(matches) == 1 else "title:" + title)
        buckets[key].append(row)
    return dict(buckets)


def counts(rows: list[dict]) -> dict:
    groups = unique_channels(rows)
    bands = dict.fromkeys(("micro", "small", "mid", "large", "unknown"), 0)
    for items in groups.values():
        values = {size_band(r.get("channel_subs")) for r in items}
        bands[next(iter(values)) if len(values) == 1 else "unknown"] += 1
    return {"channels": len(groups), "bands": bands,
            "identity_fallback": any(k.startswith("title:") for k in groups)}


def rank(snapshot: dict, catalog: dict, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    elapsed = (now - stamp(snapshot["generated_at"])).total_seconds() / 86400
    if elapsed < 0:
        raise ValueError("Snapshot is in the future")
    produced = {k for e in catalog["episodes"] for k in [e["topic_key"], *e.get("aliases", [])]}
    items = snapshot["outliers"]
    for row in items:
        for field in ("score", "age_days"):
            val = row.get(field)
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or val < 0:
                raise ValueError(f"Invalid {field}")
    coverage = snapshot.get("coverage") or {}
    complete = coverage.get("scope") == "seed_channel_sample" and "videos" in coverage
    all_rows = coverage["videos"] if complete else items
    sample_totals = None
    if complete and "channels" in coverage:
        # One synthetic identity key per sampled channel, never a fake video.
        channels = [dict(c, url=c.get("channel_id") or "channel:" + c["channel_title"].casefold())
                    for c in coverage["channels"]]
        sample_totals = counts(channels)
    candidates = []
    for cluster in DEFAULT_CLUSTERS:
        matched = list({r["url"]: r for r in items if cluster in assign(r["title"])}.values())
        if not matched:
            continue
        key, fit, exclusion = TOPICS[cluster]
        if key in produced:
            exclusion = exclusion or "Already produced (catalog key or alias)"
        groups = unique_channels(matched)
        score = median(median(r["score"] for r in group) for group in groups.values())
        observed = counts(matched)
        bands = observed["bands"]
        non_large = sum(bands[b] for b in ("micro", "small", "mid"))
        freshest = min(r["age_days"] for r in matched) + elapsed
        reasons = [exclusion] if exclusion else []
        if non_large < 2:
            reasons.append("Fewer than 2 distinct non-large channels")
        if freshest > 30:
            reasons.append("No source <=30 days at analysis time")
        if elapsed > 21:
            reasons.append("Snapshot >21 days: refresh before selection")
        candidates.append({"cluster": cluster, "topic_key": key,
            "faceless_fit_editorial": fit, "eligible": not reasons, "reasons": reasons,
            "outliers": len(matched), "outlier_channel_counts": observed,
            "observed_competition": counts([r for r in all_rows if cluster in assign(r["title"])]),
            "channel_balanced_median_score": round(score, 3),
            "freshest_age_days": round(freshest, 2),
            "median_age_days": round(median(r["age_days"] for r in matched) + elapsed, 2),
            "sources": matched})
    for candidate in candidates:
        competition = candidate["observed_competition"]
        competition["sample_channel_totals"] = sample_totals
        competition["topic_share_within_sample_by_band"] = {
            band: round(competition["bands"][band] / count, 4) if count else None
            for band, count in sample_totals["bands"].items()
        } if sample_totals else None
    candidates.sort(key=lambda c: (not c["eligible"], c["observed_competition"]["bands"]["large"],
                                  -c["channel_balanced_median_score"], c["cluster"]))
    return {"generated_at": now.isoformat(), "snapshot_at": snapshot["generated_at"],
        "scope": "seed_channel_sample" if complete else "outliers_only",
        "size_bands": "micro <10k; small 10k..100k; mid >100k..250k; large >250k; unknown separate",
        "selection_rule": "Exclude produced/adjacent themes and format labels; require >=2 non-large outlier channels and one source <=30 days; snapshot <=21 days. Then fewer large channels in observed topic coverage (outliers only in legacy snapshots), then higher channel-balanced median score. Editorial heuristic, not probability.",
        "market_saturation": None, "creator_effect_removed": False, "ctr": None,
        "limitations": ["Seed selection and survivorship bias remain", "Distinct channels are not independent experiments", "No micro/small evidence means no validation for a new channel", "Title-based grouping and duplicate screening need editorial review"],
        "selected": next((c["topic_key"] for c in candidates if c["eligible"]), None),
        "candidates": candidates}
