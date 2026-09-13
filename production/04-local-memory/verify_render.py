"""Full-decode technical QA and reproducible motion checks for Episode 4."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageChops
import yaml

from render_episode import OUT, PACKAGE, FPS, artwork, editorial_time, probe, run


def main():
    video=OUT/'04-local-memory-final.mp4'
    data=probe(video)
    timeline=json.loads((OUT/'timings.json').read_text())
    spec=yaml.safe_load((PACKAGE/'episode.yaml').read_text(encoding='utf-8'))
    v=next(s for s in data['streams'] if s['codec_type']=='video')
    a=next(s for s in data['streams'] if s['codec_type']=='audio')
    duration=float(data['format']['duration'])
    checks={
        'h264_1080p_30fps': v['codec_name']=='h264' and (v['width'],v['height'])==(1920,1080) and v['avg_frame_rate']=='30/1',
        'pixel_format': v['pix_fmt']=='yuv420p',
        'aac_48khz_stereo': a['codec_name']=='aac' and a['sample_rate']=='48000' and a['channels']==2,
        'all_twelve_scenes': len(timeline)==12,
        'audio_video_duration_match': abs(float(v['duration'])-float(a['duration']))<.12,
        'timeline_duration_match': abs(duration-sum(e['duration'] for e in timeline))<.12,
        'frame_count_match': int(v['nb_frames'])==sum(e['frames'] for e in timeline),
        'twelve_embedded_chapters':len(data['chapters'])==12,
        'first_chapter_zero':float(data['chapters'][0]['start_time'])==0,
        'chapter_intervals_at_least_10s':all(e['duration']>=10 for e in timeline),
    }
    checks['embedded_chapter_times_match']=all(abs(float(c['start_time'])-e['start'])<.01
        and c['tags']['title']==e['chapter'] for c,e in zip(data['chapters'],timeline))
    expected_chapters='\n'.join(f"{int(e['start'])//60:02d}:{int(e['start'])%60:02d} {e['chapter']}" for e in timeline)
    checks['description_chapters_match']=expected_chapters in (OUT/'description.txt').read_text()
    checks['chapters_file_match']=(OUT/'chapters.txt').read_text().strip()==expected_chapters
    checks['spoken_text_complete']=all(' '.join(c['text'] for c in entry['cues']).split()==scene['narration'].split()
                                       for scene,entry in zip(spec['scenes'],timeline))
    checks['measured_cues_contiguous']=all(abs(c['start']-(entry['cues'][i-1]['end'] if i else 0))<.001
        and 0<c['end']<=entry['duration'] for entry in timeline for i,c in enumerate(entry['cues']))
    print('FULL DECODE: checking every audio/video packet...',flush=True)
    decode=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],capture_output=True,text=True)
    checks['full_decode_without_errors']=decode.returncode==0 and not decode.stderr.strip()
    (OUT/'decode.log').write_text(decode.stderr,encoding='utf-8')
    print('AUDIO: loudness, true peak, extended silence...',flush=True)
    measured=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-af',
        'loudnorm=I=-16:TP=-1:LRA=7:print_format=json,silencedetect=noise=-45dB:d=2',
        '-f','null','-'],capture_output=True,text=True,check=True)
    loud=json.loads(measured.stderr[measured.stderr.rfind('{'):measured.stderr.rfind('}')+1])
    checks['loudness_within_1_lu']=abs(float(loud['input_i'])+16)<=1
    checks['true_peak_below_minus_1']=float(loud['input_tp'])<=-1
    checks['no_silence_longer_than_2s']='silence_start:' not in measured.stderr
    (OUT/'audio-analysis.log').write_text(measured.stderr,encoding='utf-8')
    print('MOTION: checking diagram region, excluding subtitles...',flush=True)
    holds=[]
    for scene,entry in zip(spec['scenes'],timeline):
        last=None;held=0.;worst=0.
        # Half-second sampling. Exact-state checks on source frames, not a claim
        # that random pixel noise counts as informative motion.
        for step in range(int(entry['duration']*2)):
            editorial=editorial_time(scene,entry,step/2)
            frame=artwork(scene,editorial).crop((100,300,1820,925))
            if last is not None and ImageChops.difference(last,frame).getbbox() is None:held+=.5
            else:held=0
            worst=max(worst,held);last=frame
        holds.append({'scene':scene['id'],'max_identical_hold_seconds_sampled':worst})
    checks['no_diagram_hold_over_4s']=all(h['max_identical_hold_seconds_sampled']<=4 for h in holds)
    print('FRAMES: sampling encoded MP4 at each chapter...',flush=True)
    sheet=Image.new('RGB',(1920,810),'#0b1017')
    for i,entry in enumerate(timeline):
        path=OUT/f"encoded-{entry['id']}.jpg"
        run(['ffmpeg','-y','-loglevel','error','-ss',str(entry['start']+min(3,entry['duration']/2)),
             '-i',str(video),'-frames:v','1','-q:v','2',str(path)])
        frame=Image.open(path)
        sheet.paste(frame.resize((480,270)),((i%4)*480,(i//4)*270))
    sheet.save(OUT/'encoded-contact-sheet.jpg',quality=96)
    thumb=Image.open(OUT/'thumbnail.jpg')
    checks['thumbnail_1280x720_under_2mb']=thumb.size==(1280,720) and (OUT/'thumbnail.jpg').stat().st_size<2*1024*1024
    report={'technical_pass':all(checks.values()),'checks':checks,'duration_seconds':duration,
        'audio_decoded_sha256':run(['ffmpeg','-v','error','-i',str(video),'-map','0:a:0','-f','hash','-hash','sha256','-']).strip().split('=')[-1],
        'audio_loudness_lufs':float(loud['input_i']),'audio_true_peak_dbtp':float(loud['input_tp']),
        'motion_holds':holds,'caption_alignment':'measured synthesized phrase boundaries, not word-level forced alignment',
        'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
        'thumbnail_sha256':hashlib.sha256((OUT/'thumbnail.jpg').read_bytes()).hexdigest(),
        'description_sha256':hashlib.sha256((OUT/'description.txt').read_bytes()).hexdigest(),
        'limitations':['No subjective human full-length playback certification',
                       'No hardware benchmark; calculated illustration only']}
    (OUT/'render-qa.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)
    if not report['technical_pass']:raise SystemExit(1)


if __name__=='__main__':main()
