# Episode 04 — production and explicit public release

The initial preproduction package was committed and pushed as `e5961fc` using the
user's exact requested commit message. The user subsequently authorized direct
public release of this episode. The earlier private/no-upload statements in the
historical preproduction files describe that earlier task, not the current authorization.

## Render implementation

`render_episode.py` implements all 12 layouts using code-drawn canvas primitives
regenerated at 30 fps. It uses the four executable memory-budget cases, rather
than manually authored benchmark numbers. There are no external stock assets or
competitor thumbnails in the film. The thumbnail is the original `IT FITS?` diagram.

Local Piper narration uses the existing Lessac voice at length scale 1.20. Short
phrase WAV files are cached by their exact text/configuration. Captions use measured
phrase boundaries, not estimated word alignment. Scene durations and chapters follow
those measured WAV durations. Editorial target times are retimed to the actual audio.

The hook additionally follows the measured conflict/watch/growth phrase boundaries.
Visual review caught an early reset to green during “this budget still goes red”; this
was repaired before public release and is covered by two regression tests.

The current master runs about 5:59 (359.2 seconds), 1920×1080, H.264/yuv420p,
30 fps, AAC stereo at 48 kHz. It has 12 embedded MP4 chapters and matching timestamp
lines in the description. Voice is normalized with two-pass loudness processing.

## Commands (repository root)

```powershell
docker build -f Dockerfile.video -t facelessyt-video .
docker build -f Dockerfile.episode04 -t facelessyt-episode04 .
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' -w /work facelessyt-episode04
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' -w /work --entrypoint python facelessyt-episode04 production/04-local-memory/verify_render.py
docker build -f Dockerfile.episode04qa -t facelessyt-episode04qa .
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' -w /work facelessyt-episode04qa
```

The isolated optional QA image uses local Whisper ASR to transcribe the actual
rendered audio for inspection. No audio is sent to a transcription service.
ASR is not ground truth: e.g. it transcribes “cache” as “cash” and is inconsistent
about binary-unit spellings. The spoken numerical transitions are checked against
the script and calculator; the original timed captions retain the correct spelling.

Output directory: `data/video/04-local-memory/` (ignored by Git).

- `04-local-memory-final.mp4`, `thumbnail.jpg`, `thumbnail-mobile.jpg`.
- `chapters.txt`, `description.txt`, `captions.en.srt`, `timings.json`.
- `render-qa.json`: asset hashes and technical checks.
- `encoded-contact-sheet.jpg`: samples from the encoded file, not just source art.
- `asr-review.json`: independent recognition of the rendered speech.

## Checks before publishing

The test suite includes original miner/proof/research tests, rendering tests and
episode-specific publishing tests. The animatic has 13 deterministic state checks.
The video QA fully decodes the MP4, checks codecs, frame count, A/V duration,
embedded/description chapter agreement, minimum chapter duration, measured cue
continuity, spoken text completeness, loudness/true peak, extended silence and
sampled diagram holds. Caption and diagram areas are separate. Thumbnail dimensions
and size are checked and the mobile image is inspected.

This is technical and sampled visual/editorial verification, not a claim that a
human watched the whole film or a guarantee of viewer retention. The ASR inspection
covers the full audio, but is not a subjective listening certification.

## Public publishing is episode-scoped

```powershell
# Read-only channel and duplicate check:
.\.venv\Scripts\python.exe production/04-local-memory/publish_episode.py
# Explicit public request, only after valid asset hashes and all QA checks:
.\.venv\Scripts\python.exe production/04-local-memory/publish_episode.py --public
# Confirm remote privacy/processing/metadata after insertion:
.\.venv\Scripts\python.exe production/04-local-memory/publish_episode.py --status
```

The uploader verifies the authorized channel's name AND configured channel ID,
walks its upload playlist to check duplicates, checks the final asset hashes, and
uses `privacyStatus=public` only for this explicit Episode 04 command. It does not
disable the normal private default in the project's general uploader. An in-progress
marker prevents blind retries if the upload outcome is uncertain. The returned ID
is persisted before setting the thumbnail, so a metadata failure cannot trigger a
second video insertion.

The public YouTube state must be read back: requesting public is not proof that
YouTube accepted public visibility. API-project restrictions, if any, cannot be
overridden by a local flag. Receipts and raw API status stay under ignored `data/`.
