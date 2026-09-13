"""Episode 05: measured local Piper -> original JS canvas -> FFmpeg master.

Nothing uploads or generates a thumbnail. A supplied external JPG is mandatory
for release, but the film can render while that asset is being supplied.
"""
import argparse
from array import array
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import wave

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
OUT = ROOT/'data/video/05-worker-bottleneck'
FPS = 30


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:])
    return result.stdout


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-show_chapters', '-of', 'json', str(path)]))


def phrases(text):
    result=[]
    for sentence in re.split(r'(?<=[.!?])\s+', text.strip()):
        current=[]
        for word in sentence.split():
            if current and (len(' '.join(current+[word]))>90 or len(current)>=15):
                result.append(' '.join(current));current=[]
            current.append(word)
        if current:result.append(' '.join(current))
    return result


def trim_pcm(raw, rate):
    """Remove long synthesizer margins, preserve 30/60ms leading/trailing context."""
    pcm=array('h');pcm.frombytes(raw)
    active=[i for i,x in enumerate(pcm) if abs(x)>160]
    if not active:raise ValueError('Piper returned silent speech')
    a=max(0,active[0]-round(rate*.03));b=min(len(pcm),active[-1]+1+round(rate*.06))
    return pcm[a:b].tobytes()


def tick_pcm(rate):
    pcm=array('h',[0])*(rate*3)
    for offset in (0,rate,rate*2):
        for i in range(round(rate*.07)):
            envelope=math.sin(math.pi*i/(rate*.07))**2
            pcm[offset+i]=round(32767*.025*envelope*math.sin(2*math.pi*540*i/rate))
    return pcm.tobytes()


def write_wave(path, raw, rate):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(raw)


def narration(spec):
    from piper import PiperVoice, SynthesisConfig
    folder=OUT/'audio';folder.mkdir(parents=True,exist_ok=True)
    voice=None;rate=None;entries=[];full=[];global_frame=0;countdown=None
    voice_model=os.environ['PIPER_VOICE']
    model_hash=sha(voice_model)
    for scene in spec['scenes']:
        samples=0;parts=[];captions=[];units=[]
        for index,cue in enumerate(scene['cues']):
            start_samples=samples
            if cue.get('countdown'):
                if rate is None:raise ValueError('Countdown before known audio rate')
                raw=tick_pcm(rate);parts.append(raw);samples+=len(raw)//2
                countdown=global_frame+start_samples//(rate//FPS)
            else:
                for phrase in phrases(cue['text']):
                    signature=hashlib.sha256((phrase+'|lessac|1.15|trim30-60ms|'+model_hash).encode()).hexdigest()
                    path=folder/(signature+'.wav')
                    valid=False
                    if path.exists():
                        try:
                            with wave.open(str(path),'rb') as w:
                                valid=w.getnframes()>0 and len(w.readframes(w.getnframes()))==w.getnframes()*2
                        except (EOFError,wave.Error):pass
                    if not valid:
                        if voice is None:voice=PiperVoice.load(voice_model)
                        with wave.open(str(path),'wb') as w:voice.synthesize_wav(phrase,w,SynthesisConfig(length_scale=1.15))
                    with wave.open(str(path),'rb') as w:
                        if w.getnchannels()!=1 or w.getsampwidth()!=2:raise ValueError('Unexpected Piper format')
                        current_rate=w.getframerate();raw=w.readframes(w.getnframes())
                    if rate is not None and rate!=current_rate:raise ValueError('Audio rate changed')
                    rate=current_rate
                    if rate%FPS:raise ValueError('Sample rate must divide evenly into frames')
                    raw=trim_pcm(raw,rate)
                    captions.append({'start':samples/rate,'end':(samples+len(raw)//2)/rate,'text':phrase,'source_cue':index,'wav_sha256':sha(path)})
                    parts.append(raw);samples+=len(raw)//2
            samples_per_frame=rate//FPS
            end_frame=math.ceil(samples/samples_per_frame)
            padding=end_frame*samples_per_frame-samples
            parts.append(b'\0\0'*padding);samples+=padding
            units.append({'source_cue':index,'start_frame':start_samples//samples_per_frame,'end_frame':end_frame,
                          'editorial_start':scene['start']+cue['start'],'editorial_end':scene['start']+cue['end'],
                          'countdown':bool(cue.get('countdown'))})
        raw=b''.join(parts);frames=samples//(rate//FPS)
        path=folder/(scene['id']+'.wav');write_wave(path,raw,rate);full.append(raw)
        entries.append({'id':scene['id'],'chapter':scene['chapter'],'start_frame':global_frame,'frames':frames,
                        'start':global_frame/FPS,'duration':frames/FPS,'audio':str(path),'audio_sha256':sha(path),
                        'units':units,'cues':captions})
        global_frame+=frames
        print(f"VOICE {scene['id']}: {frames/FPS:.2f}s; {len(captions)} measured phrases",flush=True)
    write_wave(OUT/'narration.wav',b''.join(full),rate)
    timeline={'fps':FPS,'frames':global_frame,'duration':global_frame/FPS,'sample_rate':rate,'countdown_start_frame':countdown,
              'countdown_frames':90,'scenes':entries,'source_spec_sha256':sha(PACKAGE/'render-spec.json'),
              'voice_model_sha256':model_hash,'voice_configuration':'Lessac medium / length_scale=1.15 / trim 30ms+60ms',
              'narration_sha256':sha(OUT/'narration.wav')}
    save(OUT/'timings.json',timeline)
    return timeline


def srt_time(seconds):
    ms=round(seconds*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def metadata(timeline):
    rows=[];meta=[';FFMETADATA1'];captions=[]
    for entry in timeline['scenes']:
        t=entry['start'];end=t+entry['duration']
        rows.append(f"{int(t)//60:02}:{int(t)%60:02} {entry['chapter']}")
        meta+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(t*1000)}',f'END={round(end*1000)}','title='+entry['chapter']]
        for cue in entry['cues']:
            captions.append(f"{len(captions)+1}\n{srt_time(t+cue['start'])} --> {srt_time(t+cue['end'])}\n{cue['text']}\n")
    (OUT/'chapters.txt').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    (OUT/'chapters.ffmeta').write_text('\n'.join(meta)+'\n',encoding='utf-8')
    (OUT/'captions.en.srt').write_text('\n'.join(captions),encoding='utf-8')
    description=("I doubled the workers from four to eight. Guess what happens before the countdown ends.\n"
        "Watch every job: preparation, waiting, tool service, and completion. Then we widen the simulated tool instead.\n\n"
        "This is a deterministic Python simulation, NOT a live AI/API benchmark. All twelve jobs arrive together. "
        "Preparation is 0.5 seconds and tool service is 2 seconds per job in the main cases. "
        "Four workers and eight workers both finish that batch in 12.5 simulated seconds with two tool slots. "
        "The peak tool queue changes from two to six. No crash, rejected connection or dropped job occurred. "
        "Gravity, warning effects and terminal jokes are editorial visualization.\n\n"
        "Code and experiment: https://github.com/tapaderuza/facelessyt/tree/main/production/05-worker-bottleneck\n"
        "Synthetic narration: local Piper, en-US Lessac. Diagram animation: original code.\n"
        "Thumbnail: AI-generated conceptual miniature, not a photographed system or a real incident.\n\n"
        "CHAPTERS\n"+'\n'.join(rows)+'\n')
    (OUT/'description.txt').write_text(description,encoding='utf-8')


def finish(timeline):
    clips=[OUT/'clips'/(e['id']+'.mp4') for e in timeline['scenes']]
    listing=OUT/'concat.txt';listing.write_text('\n'.join("file '"+p.as_posix()+"'" for p in clips),encoding='utf-8')
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(OUT/'joined-video.mp4')])
    metadata(timeline)
    first=subprocess.run(['ffmpeg','-hide_banner','-i',str(OUT/'narration.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    loud=json.loads(first.stderr[first.stderr.rfind('{'):first.stderr.rfind('}')+1])
    save(OUT/'loudness-pass1.json',loud)
    filt='loudnorm=I=-16:TP=-1.5:LRA=7:linear=true:'+':'.join(f'{dst}={loud[src]}' for dst,src in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
    target=OUT/'05-worker-bottleneck-final.mp4'
    run(['ffmpeg','-y','-v','error','-i',str(OUT/'joined-video.mp4'),'-i',str(OUT/'narration.wav'),'-i',str(OUT/'chapters.ffmeta'),
         '-map','0:v','-map','1:a','-map_metadata','2','-map_chapters','2','-c:v','copy','-af',filt,'-c:a','aac','-b:a','192k','-ar','48000','-ac','2',
         '-t',str(timeline['duration']),'-movflags','+faststart',str(target)])
    print(f"MASTER {target}: {timeline['duration']:.3f}s",flush=True)


def bundle_thumbnail(source, origin='user_supplied_external_jpg'):
    from PIL import Image
    source=Path(source).resolve()
    if not source.is_file():raise ValueError('External JPG not found')
    with Image.open(source) as im:
        if im.format!='JPEG' or im.width<640 or abs(im.width/im.height-16/9)>.02:raise ValueError('Expected an external 16:9 JPEG at least 640px wide')
    if source.stat().st_size>2*1024*1024:raise ValueError('External JPEG exceeds 2 MB; supply an optimized version')
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'thumbnail.jpg'
    if source!=target.resolve():shutil.copy2(source,target)
    save(OUT/'thumbnail-provenance.json',{'type':origin,'source_filename':source.name,'sha256':sha(target),
        'generated_by_renderer':False,'requires_visual_review':True})
    print('External thumbnail bundled without altering its pixels.',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--audio-only',action='store_true');parser.add_argument('--stills',action='store_true')
    parser.add_argument('--thumbnail');parser.add_argument('--bundle-only',action='store_true')
    parser.add_argument('--thumbnail-origin',choices=['user_supplied_external_jpg','builtin_imagegen_raster'],default='user_supplied_external_jpg')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.thumbnail:bundle_thumbnail(args.thumbnail,args.thumbnail_origin)
    if args.bundle_only:
        if not args.thumbnail:raise ValueError('--bundle-only requires --thumbnail')
        return
    spec=json.loads((PACKAGE/'render-spec.json').read_text(encoding='utf-8'))
    timeline=narration(spec)
    if args.audio_only:return
    subprocess.run(['node',str(PACKAGE/'render_video.cjs'),*(['--stills'] if args.stills else [])],check=True)
    if not args.stills:finish(timeline)


if __name__=='__main__':main()
