const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {spawn}=require('node:child_process'),{once}=require('node:events');
const {createCanvas}=require('@napi-rs/canvas');
const R=require('./renderer.js'),{locate}=require('./retime.cjs');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'data/video/05-worker-bottleneck');
const spec=JSON.parse(fs.readFileSync(path.join(__dirname,'render-spec.json'))),evidence=JSON.parse(fs.readFileSync(path.join(__dirname,'simulation-evidence.json')));
const timeline=JSON.parse(fs.readFileSync(path.join(out,'timings.json')));
const canvas=createCanvas(1920,1080),ctx=canvas.getContext('2d');
const stills=process.argv.includes('--stills');
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const codeHash=sha(fs.readFileSync(__filename)+fs.readFileSync(path.join(__dirname,'renderer.js'))+fs.readFileSync(path.join(__dirname,'retime.cjs')));
function draw(frame){const p=locate(frame,timeline);const model=R.renderFrame(ctx,p.editorialFrame,spec,evidence,{caption:p.caption,playbackRate:p.playbackRate});return {p,model};}
async function main(){
  fs.mkdirSync(path.join(out,'clips'),{recursive:true});fs.mkdirSync(path.join(out,'stills'),{recursive:true});
  const motion=[];
  for(const entry of timeline.scenes){
    const target=path.join(out,'clips',entry.id+'.mp4'),meta=target+'.json';
    const signature=sha(JSON.stringify(entry)+JSON.stringify(spec)+JSON.stringify(evidence)+codeHash);
    const reused=!stills&&fs.existsSync(target)&&fs.existsSync(meta)&&JSON.parse(fs.readFileSync(meta)).signature===signature;
    let pipe=null,error='';const errorPath=target+'.log';let completion;
    if(!stills&&!reused){
      pipe=spawn('ffmpeg',['-y','-v','error','-f','rawvideo','-pix_fmt','rgba','-s','1920x1080','-r','30','-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','18','-threads','4','-pix_fmt','yuv420p','-frames:v',String(entry.frames),target]);
      pipe.stderr.on('data',d=>error+=d);pipe.stdin.on('error',()=>{});
      completion=once(pipe,'close');
    }
    let prior=null,hold=0,worst=0;
    const sampleFrames=new Set(entry.units.flatMap(u=>[u.start_frame,Math.min(u.end_frame-1,u.start_frame+Math.round((u.end_frame-u.start_frame)/2))]));
    for(let local=0;local<entry.frames;local++){
      const frame=entry.start_frame+local;
      const {p,model:m}=draw(frame);
      const signature=JSON.stringify([m.phase,m.key,m.positions,m.rows.map(j=>j.state==='service'?m.logicalMs-j.service_start_ms:j.state==='waiting'?m.logicalMs-j.prep_end_ms:j.state==='preparing'?m.logicalMs-j.prep_start_ms:null)]);
      hold=signature===prior?hold+1:1;prior=signature;worst=Math.max(worst,hold);
      if(worst>90)throw Error('Measured semantic hold >3 s in '+entry.id);
      if(sampleFrames.has(local))fs.writeFileSync(path.join(out,'stills',entry.id+'-'+String(local).padStart(5,'0')+'.png'),await canvas.encode('png'));
      if(pipe){const pixels=ctx.getImageData(0,0,1920,1080).data;const buffer=Buffer.from(pixels.buffer,pixels.byteOffset,pixels.byteLength);if(!pipe.stdin.write(buffer))await once(pipe.stdin,'drain');}
      if(local%900===0)console.log((stills?'CHECK':'RENDER')+' '+entry.id+' '+local+'/'+entry.frames);
    }
    motion.push({scene:entry.id,max_source_semantic_hold_frames:worst});
    if(pipe){pipe.stdin.end();const [code]=await completion;fs.writeFileSync(errorPath,error);if(code!==0)throw Error(error);fs.writeFileSync(meta,JSON.stringify({signature,frames:entry.frames}));}
    console.log((reused?'CACHED':stills?'CHECKED':'ENCODED')+' '+entry.id);
  }
  fs.writeFileSync(path.join(out,'motion-qa.json'),JSON.stringify({source_pass:true,measured_timeline:true,renderer_sha256:sha(fs.readFileSync(path.join(__dirname,'renderer.js'))),timings_sha256:sha(fs.readFileSync(path.join(out,'timings.json'))),scenes:motion},null,2));
}
main().catch(e=>{console.error(e);process.exit(1);});
