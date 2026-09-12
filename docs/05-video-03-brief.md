# Episode 03 — Prove it

Working title: I Built an AI Agent That Has to Prove It's Right
Alternative: Stop Trusting Your AI Agent. Make It Prove It.

Audience: English-speaking builders making AI workflows that recommend or act on data.
Promise: build and run a small verification harness around an AI-generated recommendation;
reject missing evidence, altered arithmetic, stale snapshots, unsupported promises,
and a recommendation for a video already produced. A valid proposal must still pass.
This checks named fields, not the truth of all natural language.

Already published: episode 01 builds a YouTube outlier miner; episode 02 adds
topic history / freshness / saturation. DO NOT remake either video.
The new artifact will be a pure-Python verifier and an offline fault-injection demo.
Use existing snapshot dated 2026-09-10 (26 outliers). First row: views=182319,
channel_baseline=14416, stored score=12.65. No new YouTube data is implied.
The demo proposals are deliberately authored test fixtures, NOT observed AI failures.
Use labels in the video: "INJECTED TEST CASE" / "LOCAL REPLAY".
Passing these examples cannot establish reliability in production or guarantee views.

Creative direction: cold-open on a plausible recommendation, reveal a wrong number,
then make a visible gate reject it. Build in layers. Include a legitimate pass,
a semantic duplicate that exact keys miss, and an honest boundary on the verifier.
Move from sparse evidence cards to real terminal outputs and concise code excerpts.
Keep dark terminal + green brand, add warm red for rejection and off-white typography.
Keep text readable on mobile. No long static code walls. No dramatic fake earnings.
Produce roughly 10–14 focused minutes; this is an editorial experiment, not a claim
that the source establishes an optimal length. No padding to reach 20 minutes.

Local evidence: docs/02-hallazgos-2026-09-10.md reports harnesses: 8 outliers,
6.0x average in 5 channels. Historical observational sample, not a success forecast.
Channel screenshot: two published videos with 28 and 16 views; one subscriber.
Cannot infer CTR, retention, or traffic sources from that screenshot.

Task for reviewer: provide a Spanish editorial critique, 4 title options, one
English 30-second hook, a tight story arc and 5 concrete weaknesses to address.
Do not invent data or benchmarks. Under 900 words.
