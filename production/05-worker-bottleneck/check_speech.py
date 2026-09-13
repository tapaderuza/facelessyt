"""Independent local ASR of the encoded master; review aid, not a WER gate."""
import json
from faster_whisper import WhisperModel
from produce import ROOT, OUT, sha, save


def main():
    video = OUT / '05-worker-bottleneck-final.mp4'
    model = WhisperModel('base.en', device='cpu', compute_type='int8', cpu_threads=2,
                         download_root=str(ROOT / 'data/models/whisper'))
    segments, info = model.transcribe(str(video), language='en', beam_size=3, vad_filter=True)
    rows = []
    for segment in segments:
        rows.append({'start': segment.start, 'end': segment.end, 'text': segment.text})
        print(f'{segment.start:.1f}-{segment.end:.1f}: {segment.text}', flush=True)
    save(OUT / 'asr-review.json', {
        'language': info.language, 'segments': rows, 'video_sha256': sha(video),
        'purpose': 'Independent local ASR of rendered audio for editorial review; recognition errors are possible',
    })


if __name__ == '__main__':
    main()
