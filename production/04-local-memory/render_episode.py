"""Deterministic code-canvas Episode 4 renderer; run in facelessyt-video.

All geometry is redrawn each frame. No screenshot/zoom video. Narration is locally
synthesized in short phrases; subtitle boundaries are measured WAV boundaries,
not estimated word alignment. Outputs live under ignored data/video/04-local-memory.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from dataclasses import replace
from functools import lru_cache
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import wave

from PIL import Image, ImageDraw, ImageFont
import yaml

from facelessyt.memory_budget import Budget, GIB, calculate, demo

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
OUT = ROOT / 'data/video/04-local-memory'
W, H, FPS = 1920, 1080, 30
BG, FG, DIM, PANEL = '#0B1017', '#F3F6FA', '#A8B7CA', '#14202D'
GREEN, BLUE, RED, AMBER = '#47D18C', '#6DB5FF', '#FF5964', '#FFC857'
TITLE = "Your AI Model Fits. Your Conversation Doesn't."


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    return result.stdout


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams',
                           '-show_chapters', '-of', 'json', str(path)]))


def smooth(t):
    t = min(1., max(0., t))
    return t * t * (3 - 2 * t)


def blend(a, b, t):
    return a + (b - a) * smooth(t)


@lru_cache(maxsize=64)
def font(size, mono=False, bold=False):
    roots = ['/usr/share/fonts/truetype/dejavu', 'C:/Windows/Fonts']
    names = ([f"DejaVuSansMono{'-Bold' if bold else ''}.ttf", 'consolab.ttf' if bold else 'consola.ttf']
             if mono else [f"DejaVuSans{'-Bold' if bold else ''}.ttf", 'arialbd.ttf' if bold else 'arial.ttf'])
    for root in roots:
        for name in names:
            p = Path(root) / name
            if p.exists():
                return ImageFont.truetype(str(p), int(size))
    raise RuntimeError('No supported font')


def text(d, value, xy, size=42, color=FG, *, mono=False, bold=False, width=1700):
    f = font(size, mono, bold)
    if d.textlength(str(value), font=f) > width:
        raise ValueError(f'Text overflows: {value}')
    d.text(xy, str(value), font=f, fill=color)


def lines(d, value, xy, size=42, color=FG, width=1700, max_lines=2):
    rows, current = [], ''
    for word in str(value).split():
        attempt = (current + ' ' + word).strip()
        if d.textlength(attempt, font=font(size)) > width and current:
            rows.append(current)
            current = word
        else:
            current = attempt
    if current:
        rows.append(current)
    if len(rows) > max_lines:
        raise ValueError(f'Too many text lines: {value}')
    for i, row in enumerate(rows):
        text(d, row, (xy[0], xy[1] + i * (size + 10)), size, color, width=width)


def arrow(d, a, b, progress=1., color=BLUE):
    x = blend(a[0], b[0], progress)
    y = blend(a[1], b[1], progress)
    d.line((a[0], a[1], x, y), fill=color, width=6)
    theta = math.atan2(b[1] - a[1], b[0] - a[0])
    d.polygon([(x, y), (x-20*math.cos(theta-.5), y-20*math.sin(theta-.5)),
               (x-20*math.cos(theta+.5), y-20*math.sin(theta+.5))], fill=color)


def card(d, x, y, title, value, color=BLUE, width=500, progress=1.):
    d.rounded_rectangle((x, y, x+width, y+200), 16, fill=PANEL)
    d.line((x+20, y+190, x+20+(width-40)*smooth(progress), y+190), fill=color, width=5)
    text(d, title, (x+25, y+25), 28, DIM, mono=True, width=width-50)
    text(d, value, (x+25, y+87), 48, color, bold=True, width=width-50)


def phase(scene, t):
    times = [beat[0] for beat in scene['beats']]
    i = max(0, bisect_right(times, t)-1)
    return i, smooth((t-times[i])/2.5)


def scenario(scene_id, t):
    tokens, sequences = 8192, 1
    if scene_id == 'S01':
        tokens = 32768 if t < 3 else (8192 if t < 6 else round(blend(8192,32768,(t-6)/6)))
    elif scene_id == 'S06':
        tokens = round(blend(8192, 32768, t/12))
    elif scene_id == 'S07':
        tokens = round(blend(32768, 16384, t/5))
    elif scene_id in ('S08','S09'):
        tokens, sequences = 16384, (1 if scene_id == 'S08' and t < 5 else 2)
    return calculate(Budget(tokens=tokens, sequences=sequences))


def budget_view(d, result, t, focus=0, progress=1.):
    b = result['inputs']
    total, cache = result['total_budget_bytes']/GIB, result['cache_bytes']/GIB
    text(d, f"context = {b['tokens']:,} tokens   |   sequences = {b['sequences']}", (110,320), 42, BLUE, mono=True)
    text(d, 'WEIGHTS STAY FIXED', (110,405), 28, DIM, mono=True)
    x, y, unit = 110, 490, 165
    d.rounded_rectangle((x,y,x+unit*10,y+126), 14, fill=PANEL)
    colors = [GREEN, BLUE, '#8292A6']
    lengths = [4.,cache,1.]
    start = x
    for i,(value,color) in enumerate(zip(lengths,colors)):
        end = start+value*unit
        d.rectangle((start,y,end,y+126), fill=color)
        if focus%3 == i:
            d.line((start+8,y+116,start+8+(end-start-16)*progress,y+116),fill=FG,width=7)
        if value>=1:
            label=['WEIGHTS','CACHE','RESERVE'][i]
            if value>=2:
                text(d,f'{label}: {value:.1f}',(start+18,y+42),32,BG,bold=True,width=max(150,end-start-25))
        start=end
    ceiling=x+8*unit
    for yy in range(y-32,y+166,22):
        d.line((ceiling,yy,ceiling,yy+12),fill=FG,width=5)
    text(d,'8 GiB BUDGET',(ceiling-160,y-75),34,FG,mono=True)
    if total>8:
        d.rectangle((ceiling,y,x+total*unit,y+126),fill=RED)
        text(d,f'+{total-8:.1f}',(ceiling+10,y+46),32,BG,bold=True,width=155)
    text(d,f'4 weights + {cache:.2f} cache + 1 reserve',(110,676),38,DIM)
    text(d,f'TOTAL  {total:.2f} GiB',(110,748),63,RED if total>8 else GREEN,bold=True)
    text(d,result['status'],(900,770),32,RED if total>8 else AMBER,mono=True,width=900)


HEADLINES = {
 'S01':'THE MODEL FITS. THE WORKLOAD?', 'S02':'THREE LINES ON THE BILL',
 'S03':'THE CONVERSATION LEAVES A FOOTPRINT', 'S04':'EVERY MULTIPLICATION IS VISIBLE',
 'S05':'UNDER BUDGET IS NOT VERIFIED', 'S06':'CHANGE ONE INPUT',
 'S07':'LESS CONTEXT. MORE HEADROOM.', 'S08':'ONE MODEL. TWO CONVERSATIONS.',
 'S09':'A CALCULATION HAS BOUNDARIES', 'S10':'TEST THE WORKLOAD, NOT THE LABEL',
 'S11':'SAME WEIGHTS. DIFFERENT BUDGETS.', 'S12':'CHANGE THE INPUT. CHECK THE RESULT.'}


def artwork(scene, t, subtitle='', *, evidence=None):
    """t is editorial time within this scene; geometric state is pure/deterministic."""
    evidence = evidence or demo()
    sid = scene['id']
    im = Image.new('RGB',(W,H),BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0,0,W,7),fill=GREEN)
    text(d,'OUTLIER ENGINEERING / 04',(105,48),26,DIM,mono=True,bold=True)
    text(d,f'{int(sid[1:]):02d} / 12',(1650,48),26,DIM,mono=True)
    headline=HEADLINES[sid]
    size=66
    while d.textlength(headline,font=font(size,bold=True))>1710: size-=2
    text(d,headline,(105,118),size,FG,bold=True,width=1710)
    text(d,'ILLUSTRATIVE BUDGET / NOT A HARDWARE BENCHMARK',(110,215),29,AMBER,mono=True)
    idx,p = phase(scene,t)
    if sid in ('S01','S05','S06','S07','S08'):
        result=scenario(sid,t)
        budget_view(d,result,t,idx,p)
        if sid=='S01' and t<3:
            text(d,'OVER BUDGET',(110,850),38,RED,bold=True,width=550)
        if sid=='S05' and t>=20:
            text(d,'peak: null   speed: null   quality: not measured',(110,858),29,AMBER,mono=True)
        if sid=='S07' and t>=20:
            text(d,'Weight precision != cache precision',(110,858),32,AMBER,mono=True)
        if sid=='S08':
            text(d,'SHARED WEIGHTS / SEPARATE FULL CACHES / NO PREFIX SHARING',(110,858),27,DIM,mono=True)
            # Moving token paths distinguish sequence 1 and 2; never duplicate weights.
            for seq in range(result['inputs']['sequences']):
                xx=110+((t*.22+seq*.5)%1)*1500
                d.rounded_rectangle((xx,440+seq*18,xx+35,451+seq*18),4,fill=BLUE)
    elif sid=='S02':
        if t<14 or t>=19:
            for i,(label,value,color) in enumerate([('RESIDENT WEIGHTS','4 GiB',GREEN),('CONVERSATION CACHE','1 GiB',BLUE),('RESERVE / ASSUMED','1 GiB','#8292A6')]):
                card(d,110+i*580,350,label,value,color,progress=smooth((t-i*.6)/2.5) if idx==0 else (p if idx%3==i else 1))
            for i in range(2):arrow(d,(635+i*580,450),(675+i*580,450),smooth((t-1)/3))
            text(d,'ONE MEMORY POOL: 8 GiB',(110,650),60,FG,bold=True)
            text(d,'6 GiB calculated / 2 GiB headroom',(110,740),43,GREEN)
        else:
            card(d,180,375,'MEMORY POOL A','SYSTEM RAM',GREEN,600,p)
            card(d,1110,375,'MEMORY POOL B','GPU VRAM',BLUE,600,p)
            text(d,'+',(880,420),85,RED,bold=True)
            d.line((870,535,1000,410),fill=RED,width=9)
            text(d,'NOT ONE DEVICE',(470,685),76,RED,bold=True)
    elif sid=='S03':
        text(d,'ONE LAYER / FULL-CONTEXT CACHE',(110,310),34,DIM,mono=True)
        n=min(12,1+int(t*1.1))
        for row,label in enumerate(['KEYS','VALUES']):
            text(d,label,(110,415+row*135),34,BLUE,mono=True)
            for col in range(n):
                start=col/1.1
                xx=330+col*113
                yy=395+row*135
                scale=smooth((t-start)/.5)
                d.rounded_rectangle((xx,yy+70*(1-scale),xx+92,yy+90),9,fill=BLUE if col==n-1 else '#234C70')
                text(d,str(col+1),(xx+18,yy+27),27,FG,mono=True,width=70)
        arrow(d,(390,710),(1550,710),((t%5)/5),GREEN)
        text(d,'REUSE PREVIOUS VALUES; APPEND THE NEXT',(110,780),37,GREEN,mono=True)
        note='32 layers x 8 KV heads x 128 values x 2 bytes'
        if t>=20:note='Scope: dense full context; other cache layouts differ'
        if t>=30:note='cache_bytes = per_token * tokens * sequences'
        text(d,note,(110,865),30,DIM,mono=True)
    elif sid=='S04':
        d.rounded_rectangle((105,310,1810,850),18,fill=PANEL)
        factors=['2','32','8','128','2']
        labels=['K + V','LAYERS','KV HEADS','HEAD DIM','BYTES']
        for i,(f,label) in enumerate(zip(factors,labels)):
            x=145+i*327
            active=min(4,max(0,int(t/4)))
            text(d,label,(x,370),25,DIM,mono=True,width=300)
            text(d,f,(x,425),85,GREEN if i==active else FG,bold=True,width=240)
            if i<4:text(d,'x',(x+230,445),50,DIM,width=80)
            if i==active:d.line((x,532,x+220*p,532),fill=GREEN,width=7)
        value=evidence['short']['kv_bytes_per_token_per_sequence']
        text(d,f'= {value:,} bytes / token / sequence',(145,593),46,BLUE,mono=True)
        code='cache = per_token * tokens * sequences'
        if t>=21:
            count=min(len(code),round((t-21)*18))
            text(d,code[:count],(145,683),35,FG,mono=True)
        if t>=26:text(d,'total = weights + cache + reserve',(145,760),35,AMBER,mono=True)
    elif sid in ('S09','S10'):
        items=(['Reserve: chosen allowance, not measured overhead',
                'Download size is not resident weight size',
                'Backend buffers and allocation: not measured',
                'Offload: separate memory pools, not one sum',
                'Dense full-context cache only'] if sid=='S09' else
               ['Record model revision, format and backend',
                'Set context and simultaneous sequences',
                'Calculate the explicit memory budget',
                'Load + warm up + run the target workload',
                'Measure peak memory, latency and useful output'])
        active=min(4,idx)
        for i,item in enumerate(items):
            yy=315+i*110
            d.rounded_rectangle((110,yy,1800,yy+90),10,fill=PANEL)
            text(d,f'{i+1:02d}',(138,yy+22),33,BLUE if i!=active else AMBER,mono=True)
            text(d,item,(225,yy+25),34,FG if i<=active else DIM,width=1540)
            if i==active:d.line((225,yy+78,225+1460*p,yy+78),fill=AMBER,width=4)
        if sid=='S10' and t>=15:
            # Trace a live dependency from budget to actual measurement.
            arrow(d,(145,910),(1700,910),(t%5)/5,GREEN)
    elif sid=='S11':
        keys=['short','long','reduced_context','two_sequences']
        labels=['8,192 tokens / 1 sequence','32,768 tokens / 1 sequence','16,384 tokens / 1 sequence','16,384 tokens / 2 sequences']
        for i,(key,label) in enumerate(zip(keys,labels)):
            yy=320+i*133
            c=evidence[key]
            color=RED if c['status']=='over_budget' else GREEN
            d.rounded_rectangle((110,yy,1800,yy+112),12,fill=PANEL)
            text(d,label,(140,yy+34),36,FG,mono=True,width=1050)
            text(d,f"{c['total_budget_bytes']/GIB:.0f} GiB",(1450,yy+25),53,color,bold=True,width=320)
            d.line((1160,yy+88,1160+200*smooth((t-i*4)/2.5),yy+88),fill=color,width=7)
            if i==idx%4:
                d.line((140,yy+99,140+980*p,yy+99),fill=color,width=4)
        text(d,'CONSTANT: 4 GiB weights + 1 GiB assumed reserve',(110,885),29,DIM,mono=True)
    else:
        d.rounded_rectangle((110,320,1800,600),18,fill=PANEL)
        code='python -m facelessyt.memory_budget'
        text(d,'RUN THE REPRODUCIBLE CALCULATION',(145,355),31,DIM,mono=True)
        text(d,code[:min(len(code),int(t*20)+1)],(145,430),51,GREEN,mono=True)
        text(d,'github.com/tapaderuza/facelessyt',(110,675),51,FG,bold=True)
        text(d,'Change tokens. Then check the workload.',(110,766),45,BLUE)
        arrow(d,(120,875),(1650,875),(t%4)/4,GREEN)
    # Measured phrase subtitle, never fabricated word highlighting.
    if subtitle:
        d.rectangle((0,947,W,H),fill=BG)
        lines(d,subtitle,(110,959),44,FG,1700,2)
    return im


def phrases(narration):
    sentences=re.split(r'(?<=[.!?])\s+',narration.strip())
    result=[]
    for sentence in sentences:
        current=[]
        for word in sentence.split():
            if current and (len(' '.join(current+[word]))>100 or len(current)>=16):
                result.append(' '.join(current));current=[]
            current.append(word)
        if current:result.append(' '.join(current))
    return result


def narration_audio(spec):
    from piper import PiperVoice, SynthesisConfig
    model=os.environ['PIPER_VOICE']
    speaker=None
    audio_dir=OUT/'audio';audio_dir.mkdir(parents=True,exist_ok=True)
    timeline=[]
    for scene in spec['scenes']:
        pcm, cues, rate, elapsed=[],[],None,0.
        for i,phrase in enumerate(phrases(scene['narration'])):
            signature=hashlib.sha256((phrase+'|piper-lessac|length=1.20|v2').encode()).hexdigest()
            path=audio_dir/f'{signature}.wav'
            valid=False
            if path.exists():
                try:
                    with wave.open(str(path),'rb') as cached:
                        valid=cached.getnframes()>0 and len(cached.readframes(cached.getnframes()))==cached.getnframes()*cached.getsampwidth()*cached.getnchannels()
                except (wave.Error,EOFError):
                    valid=False
            if not valid:
                if speaker is None:speaker=PiperVoice.load(model)
                with wave.open(str(path),'wb') as wav:
                    speaker.synthesize_wav(phrase,wav,SynthesisConfig(length_scale=1.20))
            with wave.open(str(path),'rb') as wav:
                if wav.getnchannels()!=1 or wav.getsampwidth()!=2:raise ValueError('Unexpected Piper format')
                if rate is not None and rate!=wav.getframerate():raise ValueError('Audio rate changed')
                rate=wav.getframerate();raw=wav.readframes(wav.getnframes())
            duration=len(raw)/(2*rate)
            cues.append({'start':elapsed,'end':elapsed+duration,'text':phrase})
            pcm.append(raw);elapsed+=duration
        frames=math.ceil((elapsed+.15)*FPS)
        seconds=frames/FPS
        pcm.append(b'\x00\x00'*max(0,round((seconds-elapsed)*rate)))
        path=audio_dir/f"{scene['id']}.wav"
        with wave.open(str(path),'wb') as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(b''.join(pcm))
        timeline.append({'id':scene['id'],'duration':seconds,'frames':frames,'audio':str(path),
                         'cues':cues,'chapter':scene['chapter']})
        print(f"NARRATION {scene['id']}: {seconds:.2f}s, {len(cues)} measured phrases",flush=True)
    return timeline


def timestamp(sec):
    ms=round(sec*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def editorial_time(scene, entry, real):
    if scene['id']=='S01':
        watch=next(c for c in entry['cues'] if c['text'].startswith('Watch the blue section'))
        growing=next(c for c in entry['cues'] if 'a longer context' in c['text'].lower())
        growth_start=growing['start'] if growing['start']>watch['start'] else watch['start']+min(1.2,(watch['end']-watch['start'])/3)
        # Keep the red result through the spoken conflict. Replay the short case
        # only when the voice asks us to watch, then grow with the six-to-nine phrase.
        anchors=[(0.,0.),(watch['start'],3.),(growth_start,6.),(growing['end'],12.),(entry['duration'],30.)]
        for (a,x),(b,y) in zip(anchors,anchors[1:]):
            if real<b:return x+(y-x)*(real-a)/(b-a)
        return 30.
    return real/entry['duration']*(scene['end']-scene['start'])


def thumbnail():
    im=Image.new('RGB',(1280,720),BG);d=ImageDraw.Draw(im)
    x,y,u=90,180,47
    # Vertical memory container: 4 weights + 4 cache + 1 reserve > 8 ceiling.
    d.rounded_rectangle((x-20,y-90,x+450,y+460),24,fill=PANEL)
    for lower,upper,color in [(0,4,GREEN),(4,8,BLUE),(8,9,RED)]:
        yy=y+430-upper*u
        d.rounded_rectangle((x+30,yy,x+380,y+430-lower*u-6),8,fill=color)
    ceiling=y+430-8*u
    d.line((x-15,ceiling,x+438,ceiling),fill=FG,width=7)
    text(d,'MODEL',(x+63,y+300),43,BG,bold=True,width=310)
    text(d,'CONTEXT',(x+63,y+130),43,BG,bold=True,width=310)
    text(d,'IT',(640,176),145,FG,bold=True,width=550)
    text(d,'FITS?',(630,340),157,FG,bold=True,width=620)
    arrow(d,(680,170),(530,ceiling+5),1,RED)
    im.save(OUT/'thumbnail.jpg',quality=96)
    im.resize((320,180),Image.Resampling.LANCZOS).save(OUT/'thumbnail-mobile.jpg',quality=95)


def render(spec,timeline,preview=False,only_scene=None):
    clips=OUT/'clips';clips.mkdir(exist_ok=True)
    scenes=spec['scenes'][:1] if preview else spec['scenes']
    paths=[]
    for scene,entry in zip(scenes,timeline):
        path=clips/f"{scene['id']}.mp4";meta=path.with_suffix('.json')
        if only_scene and scene['id']!=only_scene:
            if not path.exists() or abs(float(probe(path)['format']['duration'])-entry['duration'])>.1:
                raise ValueError('Cannot reuse missing or mismatched unaffected scene')
            paths.append(path);print(f"REUSE UNCHANGED {scene['id']}",flush=True);continue
        sig=hashlib.sha256((Path(__file__).read_text()+json.dumps(scene)+json.dumps(entry)).encode()).hexdigest()
        if path.exists() and meta.exists() and json.loads(meta.read_text()).get('signature')==sig:
            paths.append(path);print(f"CACHED {scene['id']}",flush=True);continue
        error=clips/f"{scene['id']}.ffmpeg.log"
        with error.open('wb') as err:
            proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24',
                '-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',entry['audio'],
                '-map','0:v','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','18',
                '-threads','4','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',
                '-t',str(entry['duration']),str(path)],stdin=subprocess.PIPE,stderr=err)
            starts=[c['start'] for c in entry['cues']]
            try:
                for frame in range(entry['frames']):
                    real=frame/FPS
                    editorial=editorial_time(scene,entry,real)
                    ci=max(0,bisect_right(starts,real)-1);cue=entry['cues'][ci]
                    caption=cue['text'] if real<cue['end'] else ''
                    image=artwork(scene,editorial,caption)
                    proc.stdin.write(image.tobytes())
                proc.stdin.close()
                rc=proc.wait()
                if rc:raise RuntimeError(error.read_text()[-2500:])
            except BaseException:
                proc.kill();proc.wait();raise
        actual=float(probe(path)['format']['duration'])
        if abs(actual-entry['duration'])>.1:raise ValueError('Clip duration mismatch')
        meta.write_text(json.dumps({'signature':sig,'duration':actual}),encoding='utf-8')
        paths.append(path);print(f"RENDERED {scene['id']}: {entry['frames']} frames",flush=True)
    listing=OUT/'concat.txt';listing.write_text('\n'.join(f"file '{p.as_posix()}'" for p in paths),encoding='utf-8')
    joined=OUT/'joined.mp4'
    run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(joined)])
    entries=timeline[:1] if preview else timeline
    elapsed,captions,chapters,metadata=0.,[],[],[';FFMETADATA1']
    for entry in entries:
        entry['start']=elapsed
        chapters.append(f"{int(elapsed)//60:02d}:{int(elapsed)%60:02d} {entry['chapter']}")
        metadata += ['[CHAPTER]','TIMEBASE=1/1000',f'START={round(elapsed*1000)}',
                     f"END={round((elapsed+entry['duration'])*1000)}",f"title={entry['chapter']}"]
        for cue in entry['cues']:
            captions.append(f"{len(captions)+1}\n{timestamp(elapsed+cue['start'])} --> {timestamp(elapsed+cue['end'])}\n{cue['text']}\n")
        elapsed+=entry['duration']
    (OUT/'chapters.txt').write_text('\n'.join(chapters)+'\n',encoding='utf-8')
    (OUT/'captions.en.srt').write_text('\n'.join(captions),encoding='utf-8')
    (OUT/'timings.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
    chapter_meta=OUT/'chapters.ffmeta';chapter_meta.write_text('\n'.join(metadata),encoding='utf-8')
    # Two-pass loudness normalization against the actual full narration.
    first=subprocess.run(['ffmpeg','-hide_banner','-i',str(joined),'-af','loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json',
                          '-f','null','-'],capture_output=True,text=True,check=True)
    loud=json.loads(first.stderr[first.stderr.rfind('{'):first.stderr.rfind('}')+1])
    filt=('loudnorm=I=-16:TP=-1.5:LRA=7:linear=true:'+
          ':'.join(f'{dst}={loud[src]}' for dst,src in [('measured_I','input_i'),('measured_TP','input_tp'),
          ('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')]))
    target=OUT/('hook-preview.mp4' if preview else '04-local-memory-final.mp4')
    run(['ffmpeg','-y','-loglevel','error','-i',str(joined),'-i',str(chapter_meta),'-map','0:v','-map','0:a',
         '-map_metadata','1','-map_chapters','1','-c:v','copy','-af',filt,'-c:a','aac','-b:a','192k',
         '-ar','48000','-ac','2','-movflags','+faststart',str(target)])
    (OUT/'loudness-pass1.json').write_text(json.dumps(loud,indent=2),encoding='utf-8')
    description=("A local AI model can fit while its workload exceeds the memory budget.\n"
        "We build an executable Python illustration and change context length and simultaneous sequences.\n\n"
        "Run the code: https://github.com/tapaderuza/facelessyt/blob/main/src/facelessyt/memory_budget.py\n"
        "Repository and setup: https://github.com/tapaderuza/facelessyt\n\n"
        "IMPORTANT: This is a synthetic budget calculation, NOT a hardware benchmark. No LLM was loaded. "
        "The 4 GiB resident weights, 1 GiB reserve and 8 GiB memory pool are illustrative inputs. "
        "The formula assumes dense full-context KV tensors; it does not certify all model architectures, "
        "real peak memory, performance or output quality. RAM and VRAM are not added as one pool.\n\n"
        "Technical references:\nhttps://huggingface.co/docs/transformers/main/en/cache_explanation\n"
        "https://huggingface.co/docs/transformers/v4.50.0/kv_cache\n\n"
        "Narration: synthetic voice, Piper (en-US Lessac). Original diagrams are generated by code.\n\n"
        "CHAPTERS\n"+'\n'.join(chapters)+'\n')
    (OUT/'description.txt').write_text(description,encoding='utf-8')
    print(f'COMPLETE {target} | {elapsed:.2f}s',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true')
    parser.add_argument('--stills',action='store_true')
    parser.add_argument('--only-scene',choices=['S01'],help='Repair hook timing; explicitly reuse the unchanged other scenes')
    args=parser.parse_args()
    spec=yaml.safe_load((PACKAGE/'episode.yaml').read_text(encoding='utf-8'))
    if json.loads((PACKAGE/'memory-evidence.json').read_text())!=demo():raise ValueError('Evidence drift')
    OUT.mkdir(parents=True,exist_ok=True);thumbnail()
    for scene in spec['scenes']:
        for t in [0,*(b[0]+1.5 for b in scene['beats'])]:
            artwork(scene,t,'Measured phrase subtitles stay in this reserved area.').save(OUT/f"{scene['id']}-check.png")
    if args.stills:
        sheet=Image.new('RGB',(1920,1080),BG)
        for i,scene in enumerate(spec['scenes']):
            im=Image.open(OUT/f"{scene['id']}-check.png").resize((480,270))
            sheet.paste(im,((i%4)*480,(i//4)*270))
        sheet.save(OUT/'contact-sheet.jpg',quality=95)
        print('STILLS: all layouts and beats checked');return
    timeline=narration_audio(spec)
    render(spec,timeline,args.preview,args.only_scene)


if __name__=='__main__':main()
