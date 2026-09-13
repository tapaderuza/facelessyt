// Local read-only browser QA over CDP. Dedicated headless Edge profile only.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'data/qa-episode05');
const port=Number(process.argv[2]||18765);
async function connect(url){
  const ws=new WebSocket(url);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  let seq=0;const pending=new Map(),errors=[];
  ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);if(!p)return;pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}
    else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);};
  return {ws,errors,call(method,params={}){return new Promise((resolve,reject)=>{const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP timeout '+method));},10000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));});}};
}
(async()=>{
  const pages=await(await fetch('http://127.0.0.1:'+port+'/json/list')).json();
  const page=pages.find(p=>p.type==='page');assert.ok(page);
  const c=await connect(page.webSocketDebuggerUrl);
  const evaluate=async expression=>{const r=await c.call('Runtime.evaluate',{expression,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
  await c.call('Page.enable');await c.call('Runtime.enable');
  await c.call('Page.navigate',{url:'file:///'+path.join(__dirname,'lab.html').replaceAll('\\','/')});
  let ready=false;for(let i=0;i<50;i++){if(await evaluate('Boolean(window.episode05)')){ready=true;break;}await new Promise(r=>setTimeout(r,100));}assert.ok(ready);
  const seek=async frame=>evaluate(`document.getElementById('seek').value=${frame};document.getElementById('seek').dispatchEvent(new Event('input'));true`);
  await evaluate("document.getElementById('challenge').click();document.getElementById('guessB').click();true");
  assert.match(await evaluate("document.getElementById('guess').textContent"),/Locked in: B/);
  await seek(3960);
  assert.doesNotMatch(await evaluate("document.getElementById('guess').textContent"),/12.5|NOT CRASH/);
  await c.call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
  fs.mkdirSync(out,{recursive:true});
  const save=async name=>{const shot=await c.call('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,name),Buffer.from(shot.data,'base64'));};
  await save('browser-countdown.png');
  await seek(4080);assert.equal(await evaluate("document.getElementById('guessA').disabled"),true);await save('browser-jam.png');
  await seek(4350);assert.match(await evaluate("document.getElementById('guess').textContent"),/12.5/);
  await evaluate("document.getElementById('reduced').checked=true;document.getElementById('reduced').dispatchEvent(new Event('change'));true");
  assert.deepEqual(await evaluate("(()=>{const m=window.episode05.renderFrame(4065,true);return [m.shake,m.warningAlpha]})()"),[0,0]);
  await evaluate("document.getElementById('sound').checked=false;document.getElementById('play').click();true");
  await new Promise(r=>setTimeout(r,150));
  await evaluate("document.getElementById('play').click();true");
  assert.equal(await evaluate("document.getElementById('play').textContent"),'Play');
  await c.call('Emulation.setDeviceMetricsOverride',{width:375,height:900,deviceScaleFactor:1,mobile:true});
  await seek(3980);await save('browser-mobile-countdown.png');
  const overflow=await evaluate('document.documentElement.scrollWidth>innerWidth');
  assert.equal(overflow,false);assert.deepEqual(c.errors,[]);
  const report={browser:'dedicated headless Edge',console_exceptions:c.errors,guess_selection:true,guess_locks_after_countdown:true,no_early_answer:true,answer_after_completion:true,reduced_motion:true,play_pause:true,mobile_horizontal_overflow:overflow,
    screenshots:['browser-countdown.png','browser-jam.png','browser-mobile-countdown.png'],visual_regression:'INCONCLUSIVE: no baseline',limitations:['No tick listening check','No accessibility certification','No final MP4 or measured narration']};
  fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
  await c.call('Browser.close');c.ws.close();
})().catch(e=>{console.error(e);process.exitCode=1;});
