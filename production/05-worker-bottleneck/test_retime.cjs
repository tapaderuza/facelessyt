const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {locate}=require('./retime.cjs'),R=require('./renderer.js');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'data/video/05-worker-bottleneck');
const timeline=JSON.parse(fs.readFileSync(path.join(out,'timings.json'))),spec=JSON.parse(fs.readFileSync(path.join(__dirname,'render-spec.json'))),evidence=JSON.parse(fs.readFileSync(path.join(__dirname,'simulation-evidence.json')));
let count=0,first=null,last=null;
for(let f=0;f<timeline.frames;f++){
  const p=locate(f,timeline),m=R.frameModel(p.editorialFrame,spec,evidence);
  assert.equal(m.scene.id,p.entry.id);
  assert.equal(m.cue.visual,spec.scenes.find(s=>s.id===p.entry.id).cues[p.unit.source_cue].visual);
  if(m.phase==='countdown'){count++;first=first??f;last=f;assert.equal(p.caption,'');assert.equal(m.resultVisible,false);}
  if(p.entry.id==='S05'&&p.unit.source_cue<4)assert.equal(m.answerVisible,false);
  if(p.entry.id==='S05'&&p.unit.source_cue===4)assert.equal(m.answerVisible,true);
}
assert.equal(count,90);assert.equal(first,timeline.countdown_start_frame);assert.equal(last-first+1,90);
assert.equal(R.frameModel(locate(first,timeline).editorialFrame,spec,evidence).countdown,3);
assert.equal(R.frameModel(locate(first+30,timeline).editorialFrame,spec,evidence).countdown,2);
assert.equal(R.frameModel(locate(first+60,timeline).editorialFrame,spec,evidence).countdown,1);
console.log(JSON.stringify({measured_retiming_pass:true,frames:timeline.frames,countdown_frames:count,actual_countdown_start:first/30,duration:timeline.duration},null,2));
