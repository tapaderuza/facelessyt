"""Verify the encoded Episode 05 master, not just the authored timeline."""
import argparse
from array import array
import json
from pathlib import Path
import re
import subprocess
import wave
from PIL import Image
from produce import OUT, PACKAGE, sha, save, probe, run


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--video-only',action='store_true');args=parser.parse_args()
    video=OUT/'05-worker-bottleneck-final.mp4'
    timeline=json.loads((OUT/'timings.json').read_text())
    spec=json.loads((PACKAGE/'render-spec.json').read_text())
    motion=json.loads((OUT/'motion-qa.json').read_text())
    data=probe(video);v=next(s for s in data['streams'] if s['codec_type']=='video');a=next(s for s in data['streams'] if s['codec_type']=='audio')
    duration=float(data['format']['duration'])
    checks={
        'h264_1080p_30fps':v['codec_name']=='h264' and (v['width'],v['height'])==(1920,1080) and v['avg_frame_rate']=='30/1',
        'yuv420p':v['pix_fmt']=='yuv420p',
        'aac_stereo_48k':a['codec_name']=='aac' and a['channels']==2 and a['sample_rate']=='48000',
        'duration_matches_measured_voice':abs(duration-timeline['duration'])<.12,
        'audio_video_match':abs(float(v['duration'])-float(a['duration']))<.12,
        'frame_count':int(v['nb_frames'])==timeline['frames'],
        'eight_chapters':len(data['chapters'])==8,
        'chapters_match_measured_timeline':len(data['chapters'])==len(timeline['scenes']) and all(abs(float(c['start_time'])-e['start'])<.01 and c['tags']['title']==e['chapter'] for c,e in zip(data['chapters'],timeline['scenes'])),
        'chapter_rules':timeline['scenes'][0]['start']==0 and all(e['duration']>=10 for e in timeline['scenes']),
        'source_hash_matches':timeline['source_spec_sha256']==sha(PACKAGE/'render-spec.json'),
        'narration_hash_matches':timeline['narration_sha256']==sha(OUT/'narration.wav'),
        'motion_qa_matches_renderer_and_audio_timing':motion['renderer_sha256']==sha(PACKAGE/'renderer.js') and motion['timings_sha256']==sha(OUT/'timings.json'),
        'semantic_hold_at_most_3s':motion['source_pass'] and all(s['max_source_semantic_hold_frames']<=90 for s in motion['scenes']),
    }
    expected='\n'.join(f"{int(e['start'])//60:02}:{int(e['start'])%60:02} {e['chapter']}" for e in timeline['scenes'])
    checks['chapters_text_and_description']=expected==(OUT/'chapters.txt').read_text().strip() and expected in (OUT/'description.txt').read_text()
    checks['all_spoken_words_preserved']=all(' '.join(c['text'] for c in e['cues']).split()==' '.join(c['text'] for c in scene['cues']).split() for scene,e in zip(spec['scenes'],timeline['scenes']))
    checks['measured_phrase_ranges']=all(0<=c['start']<c['end']<=e['duration'] for e in timeline['scenes'] for c in e['cues'])
    checks['unit_continuity']=all(e['units'][0]['start_frame']==0 and e['units'][-1]['end_frame']==e['frames'] and all(x['end_frame']==y['start_frame'] for x,y in zip(e['units'],e['units'][1:])) for e in timeline['scenes'])
    units=[(e,u) for e in timeline['scenes'] for u in e['units'] if u['countdown']]
    checks['countdown_exactly_90_frames']=len(units)==1 and units[0][1]['end_frame']-units[0][1]['start_frame']==90
    start=timeline['countdown_start_frame']/30;end=start+3
    checks['no_narration_during_countdown']=not any(e['start']+c['start']<end and e['start']+c['end']>start for e in timeline['scenes'] for c in e['cues'])
    with wave.open(str(OUT/'narration.wav'),'rb') as wav:
        rate=wav.getframerate();wav.setpos(round(start*rate));pcm=array('h');pcm.frombytes(wav.readframes(rate*3))
    checks['three_source_tick_windows']=all(max(abs(x) for x in pcm[i*rate:i*rate+round(rate*.07)])>100 and not any(pcm[i*rate+round(rate*.07):(i+1)*rate]) for i in range(3))
    print('FULL DECODE...',flush=True)
    decode=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],capture_output=True,text=True)
    checks['full_decode']=decode.returncode==0 and not decode.stderr.strip();(OUT/'decode.log').write_text(decode.stderr)
    print('ENCODED AUDIO...',flush=True)
    audio=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-af','loudnorm=I=-16:TP=-1:LRA=7:print_format=json,silencedetect=noise=-45dB:d=2','-f','null','-'],capture_output=True,text=True,check=True)
    loud=json.loads(audio.stderr[audio.stderr.rfind('{'):audio.stderr.rfind('}')+1])
    (OUT/'audio-analysis.log').write_text(audio.stderr)
    checks['loudness']=abs(float(loud['input_i'])+16)<=1;checks['true_peak']=float(loud['input_tp'])<=-1
    checks['no_unintended_silence_over_2s']='silence_start:' not in audio.stderr
    print('ENCODED MOTION SAMPLES...',flush=True)
    pixels=subprocess.run(['ffmpeg','-v','error','-i',str(video),'-an','-vf','crop=1820:690:50:190,scale=320:122,fps=10','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True,check=True).stdout
    size=320*122;last=None;held=0;worst=0
    for offset in range(0,len(pixels)-size+1,size):
        frame=pixels[offset:offset+size]
        difference=sum(abs(x-y) for x,y in zip(frame,last))/size if last else 255
        held=held+1 if difference<.015 else 0;worst=max(worst,held);last=frame
    checks['encoded_no_frozen_roi_over_3s']=worst<=30
    sheet=Image.new('RGB',(1920,1080),'#0b1119')
    samples=[(e['id'],e['start']+min(3,e['duration']/2)) for e in timeline['scenes']]
    samples += [('count3',start+.2),('count2',start+1.2),('count1',start+2.2),('jam',end+.7)]
    for i,(name,t) in enumerate(samples):
        path=OUT/('encoded-'+name+'.jpg')
        run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-q:v','2',str(path)])
        with Image.open(path) as im:sheet.paste(im.resize((480,270)),((i%4)*480,(i//4)*270))
    sheet.save(OUT/'encoded-contact-sheet.jpg',quality=95)
    video_checks_pass=all(checks.values())
    thumbnail_sha=None
    if not args.video_only:
        thumb=OUT/'thumbnail.jpg';provenance=OUT/'thumbnail-provenance.json'
        valid=thumb.exists() and provenance.exists()
        if valid:
            p=json.loads(provenance.read_text());thumbnail_sha=sha(thumb)
            with Image.open(thumb) as im:valid=im.format=='JPEG' and im.width>=640 and abs(im.width/im.height-16/9)<.02 and thumb.stat().st_size<2*1024*1024
            valid=valid and p['generated_by_renderer'] is False and p['sha256']==thumbnail_sha
        checks['external_jpg_thumbnail']=valid
    report={'technical_pass':not args.video_only and all(checks.values()),'video_checks_pass':video_checks_pass,'checks':checks,
        'duration_seconds':duration,'video_sha256':sha(video),'thumbnail_sha256':thumbnail_sha,'description_sha256':sha(OUT/'description.txt'),
        'audio_lufs':float(loud['input_i']),'audio_true_peak_dbtp':float(loud['input_tp']),
        'audio_decoded_sha256':run(['ffmpeg','-v','error','-i',str(video),'-map','0:a:0','-f','hash','-hash','sha256','-']).strip().split('=')[-1],
        'sampled_encoded_max_hold_seconds':worst/10,'countdown_start_seconds':start,
        'limitations':['Frame-level narration boundaries measured; not word-level forced alignment','Technical and sampled visual checks are not a subjective full-length human playback certification']}
    save(OUT/('video-qa.json' if args.video_only else 'render-qa.json'),report);print(json.dumps(report,indent=2),flush=True)
    if not all(checks.values()):raise SystemExit(1)


if __name__=='__main__':main()
