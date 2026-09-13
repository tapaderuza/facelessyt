// Exercise every frame with a stub canvas; browser screenshots are separate QA.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const R=require('./renderer.js');
const spec=JSON.parse(fs.readFileSync(path.join(__dirname,'render-spec.json'),'utf8'));
const evidence=JSON.parse(fs.readFileSync(path.join(__dirname,'simulation-evidence.json'),'utf8'));
let checks=0,ops=[];
const ctx=new Proxy({measureText:s=>({width:s.length*20})},{get:(o,k)=>o[k]||((...a)=>ops.push([k,...a])),set:()=>true});
let maxFrozen=0,frozen=0,lastSignature=null,countdownFrames=0;
for(let f=0;f<spec.target_seconds*spec.fps;f++){
  ops=[];const m=R.renderFrame(ctx,f,spec,evidence);
  assert.equal(Object.values(m.counts).reduce((a,b)=>a+b,0),m.trace.inputs.jobs);checks++;
  assert.ok(m.counts.service<=m.trace.inputs.tool_slots);checks++;
  assert.ok(Math.abs(m.shake)<=3);checks++;
  assert.ok(m.warningAlpha<=0.18);checks++;
  assert.ok(m.positions.every(p=>p.x>=80&&p.x<=1840&&p.y>=190&&p.y<=800));checks++;
  const owned=m.rows.filter(j=>['preparing','waiting','service'].includes(j.state)).map(j=>j.worker);
  assert.equal(new Set(owned).size,owned.length);checks++;
  // Source semantic signature: meaningful task positions, waits and service progress only.
  const signature=JSON.stringify([m.phase,m.key,m.positions,m.rows.map(j=>j.state==='service'?m.logicalMs-j.service_start_ms:j.state==='waiting'?m.logicalMs-j.prep_end_ms:j.state==='preparing'?m.logicalMs-j.prep_start_ms:null)]);
  frozen=signature===lastSignature?frozen+1:1;lastSignature=signature;maxFrozen=Math.max(maxFrozen,frozen);
  if(m.phase==='countdown'){
    countdownFrames++;
    assert.equal(m.logicalMs,0);assert.equal(m.cue.text,'');assert.equal(m.answerVisible,false);
    assert.equal(m.resultVisible,false);assert.equal(m.egg,null);checks+=5;
  }
  if(m.scene.id==='S05'&&m.time<145){assert.equal(m.answerVisible,false);assert.equal(m.resultVisible,false);checks+=2;}
}
assert.equal(countdownFrames,90);checks++;
assert.ok(maxFrozen<=90,'semantic hold exceeds 3 s: '+maxFrozen);checks++;
for(const [t,n] of [[132,3],[133,2],[134,1],[134.9666666667,1]]){
  assert.equal(R.frameModel(Math.round(t*30),spec,evidence).countdown,n);checks++;
}
assert.equal(R.frameModel(135*30,spec,evidence).phase,'run');checks++;
assert.equal(R.frameModel(145*30,spec,evidence).answerVisible,true);checks++;
assert.equal(R.frameModel(145*30,spec,evidence).logicalMs,12500);checks++;
assert.deepEqual(R.tickEvents(spec).map(t=>t.frame),[3960,3990,4020]);checks++;
const impactFrame=135*30+15;
const a=R.frameModel(impactFrame,spec,evidence),b=R.frameModel(impactFrame,spec,evidence,true);
assert.equal(b.shake,0);assert.equal(b.warningAlpha,0);assert.deepEqual(a.counts,b.counts);checks+=3;
assert.ok(a.positions===undefined);checks++;
const snapshot=JSON.stringify(evidence);
R.renderFrame(ctx,impactFrame,spec,evidence);assert.equal(JSON.stringify(evidence),snapshot);checks++;
ops=[];R.renderFrame(ctx,impactFrame,spec,evidence);const draw=JSON.stringify(ops);
ops=[];R.renderFrame(ctx,impactFrame,spec,evidence);assert.equal(JSON.stringify(ops),draw);checks++;
const waiting=a.rows.find(j=>j.state==='waiting');
assert.notDeepEqual(R.tilePosition(waiting,a,spec),R.tilePosition(waiting,b,spec));checks++;
console.log(JSON.stringify({assertions_passed:checks,frames_rendered:7200,countdown_frames:countdownFrames,max_source_semantic_hold_frames:maxFrozen,scope:'stub canvas + source state, not encoded MP4 or accessibility certification'},null,2));
