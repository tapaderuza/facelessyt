"""Transcribe the actual rendered audio for editorial inspection. Not a WER gate."""
import json
import argparse
import hashlib
from pathlib import Path
from faster_whisper import WhisperModel

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/video/04-local-memory'
parser=argparse.ArgumentParser()
parser.add_argument('--warmup',action='store_true')
args=parser.parse_args()
model=WhisperModel('base.en',device='cpu',compute_type='int8',cpu_threads=2,
                   download_root=str(ROOT/'data/models/whisper'))
if args.warmup:
    print('Local speech-recognition model ready.',flush=True)
    raise SystemExit(0)
segments,info=model.transcribe(str(OUT/'04-local-memory-final.mp4'),language='en',beam_size=3,vad_filter=True)
rows=[]
for segment in segments:
    rows.append({'start':segment.start,'end':segment.end,'text':segment.text})
    print(f'{segment.start:.1f}-{segment.end:.1f}: {segment.text}',flush=True)
(OUT/'asr-review.json').write_text(json.dumps({'language':info.language,'segments':rows,
    'video_sha256':hashlib.sha256((OUT/'04-local-memory-final.mp4').read_bytes()).hexdigest(),
    'purpose':'Independent local ASR of rendered audio for review; recognition errors are possible'},indent=2),encoding='utf-8')
