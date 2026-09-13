/* Deterministic canvas renderer. Physics is presentation only; trace owns truth.
 * Browser and Node share this module. No live APIs or wall-clock physics.
 */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.Episode05Renderer=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const C={input:'#91a5b7',preparing:'#6bb7ff',waiting:'#ffb54d',service:'#f0f4fa',done:'#42d392'};
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  function states(trace,t){return trace.jobs.map(j=>({...j,state:t<j.prep_start_ms?'input':t<j.prep_end_ms?'preparing':t<j.service_start_ms?'waiting':t<j.complete_ms?'service':'done'}));}
  function playback(trace,elapsed,speed,offset=0){
    const span=trace.metrics.batch_ms+750,raw=Math.max(0,elapsed)*1000*speed+offset;
    return {logicalMs:Math.min(trace.metrics.batch_ms,raw%span),replay:raw>=span,completedOnce:raw>=trace.metrics.batch_ms,speed};
  }
  function frameModel(frame,spec,evidence,reducedMotion=false){
    if(!Number.isInteger(frame)||frame<0||frame>=spec.target_seconds*spec.fps)throw Error('frame out of range');
    const time=frame/spec.fps,scene=spec.scenes.find(s=>time>=s.start&&time<s.end),local=time-scene.start;
    const cue=scene.cues.find(c=>local>=c.start&&local<c.end),challenge=spec.challenge;
    let key=scene.case,elapsed=local,phase='run',countdown=null,pb,answerVisible=false;
    for(const c of scene.cues){if(c.start<=local&&c.case_override){key=c.case_override;elapsed=local-c.start;}}
    if(scene.playback.challenge){
      if(time<challenge.pause_start){phase='question';key='baseline';pb=playback(evidence.cases[key],local,1);}
      else if(time<challenge.reveal_start){phase='countdown';key=scene.case;pb={logicalMs:challenge.frozen_logical_time_ms,replay:false,speed:0};countdown=Math.ceil(challenge.reveal_start-time);}
      else {key=scene.case;pb=playback(evidence.cases[key],time-challenge.trace_run_video_start,challenge.trace_speed);answerVisible=time>=challenge.answer_highlight_not_before;}
    }else {
      pb=playback(evidence.cases[key],elapsed,scene.playback.speed,scene.playback.offset_ms);
      const segment=(scene.playback.segments||[]).find(s=>local>=s.start&&local<s.end);
      if(segment){const p=(local-segment.start)/(segment.end-segment.start);pb={logicalMs:segment.from_ms+p*(segment.to_ms-segment.from_ms),speed:(segment.to_ms-segment.from_ms)/1000/(segment.end-segment.start),replay:!!segment.replay,completedOnce:false};}
    }
    const trace=evidence.cases[key],rows=states(trace,pb.logicalMs),counts=Object.fromEntries(Object.keys(C).map(k=>[k,rows.filter(j=>j.state===k).length]));
    const egg=spec.easter_eggs.find(e=>e.scene===scene.id&&local>=e.at&&local<e.until);
    // A single onset impulse per replay; only a genuinely deep queue triggers it.
    const onset=trace.jobs.filter(j=>j.service_start_ms>j.prep_end_ms).map(j=>j.prep_end_ms);
    const first=onset.length?Math.min(...onset):Infinity;
    const impactAge=(pb.logicalMs-first)/1000/(pb.speed||1);
    const stressed=counts.waiting>=4&&phase==='run';
    const shake=(!reducedMotion&&stressed&&impactAge>=0&&impactAge<spec.effects.shake.duration_s)?
      spec.effects.shake.max_px*Math.sin(impactAge*65)*Math.exp(-impactAge*10):0;
    const warningAlpha=!reducedMotion&&stressed?spec.effects.warning.max_opacity*(0.5-0.5*Math.cos(2*Math.PI*local/spec.effects.warning.pulse_period_s)):0;
    const resultVisible=answerVisible||(!scene.playback.challenge&&scene.playback.results&&pb.completedOnce);
    return {frame,time,scene,local,cue,key,trace,rows,counts,phase,countdown,answerVisible,resultVisible,
      logicalMs:pb.logicalMs,speed:pb.speed,replay:pb.replay,egg:phase==='countdown'?null:egg,
      shake,warningAlpha,reducedMotion,disclosure:spec.disclosure};
  }
  function target(j,rows){
    const peers=rows.filter(r=>r.state===j.state),i=peers.findIndex(r=>r.id===j.id);
    if(j.state==='input')return [140+(i%2)*100,300+Math.floor(i/2)*58];
    if(j.state==='preparing')return [500,285+j.worker*66];
    if(j.state==='waiting')return [820+(i%2)*100,735-Math.floor(i/2)*72];
    if(j.state==='service')return [1240,330+j.slot*112];
    return [1600+(i%3)*90,320+Math.floor(i/3)*68];
  }
  function tilePosition(j,model,spec){
    const point=target(j,model.rows);
    if(model.reducedMotion)return point;
    if(j.state!=='waiting'){
      const boundary={preparing:j.prep_start_ms,service:j.service_start_ms,done:j.complete_ms}[j.state];
      const age=(model.logicalMs-boundary)/1000/(model.speed||1);
      if(boundary>0&&age>=0&&age<0.18){
        const before=states(model.trace,boundary-0.001),origin=target(before.find(p=>p.id===j.id),before);
        const p=age/0.18;return [origin[0]+(point[0]-origin[0])*p,origin[1]+(point[1]-origin[1])*p];
      }
      return point;
    }
    // Analytic gravity drop and damped impact rebound; all seeking is reproducible.
    // Jobs in a simultaneous wave share displacement, preserving stack separation.
    const releases=model.trace.jobs.filter(q=>q.service_start_ms>q.prep_end_ms&&q.service_start_ms<=model.logicalMs).map(q=>q.service_start_ms);
    const changed=Math.max(j.prep_end_ms,...releases);
    const age=Math.max(0,(model.logicalMs-changed)/1000/(model.speed||1));
    let drop=140;
    if(changed>j.prep_end_ms){
      const previous=states(model.trace,changed-0.001),old=target(previous.find(q=>q.id===j.id),previous);
      drop=Math.max(0,point[1]-old[1]);
    }
    const g=spec.effects.physics.gravity_px_s2,hit=Math.sqrt(2*drop/g);
    const displacement=age<hit?-drop+0.5*g*age*age:
      -drop*spec.effects.physics.restitution*Math.exp(-12*(age-hit))*Math.abs(Math.sin(22*(age-hit)));
    return [point[0],point[1]+displacement];
  }
  function tickEvents(spec){return [0,1,2].map(i=>({frame:(spec.challenge.pause_start+i)*spec.fps,type:'countdown_tick',duration_ms:70,gain:0.025}));}
  function text(ctx,s,x,y,size=32,color='#eef4fb'){ctx.fillStyle=color;ctx.font=`${size}px "DejaVu Sans Mono", monospace`;ctx.fillText(s,x,y);}
  function wrapped(ctx,s,x,y,width,size=34,maxLines=2){
    ctx.font=`${size}px "DejaVu Sans Mono", monospace`;let line='',lines=[];
    for(const word of s.split(/\s+/)){const next=line?line+' '+word:word;if(ctx.measureText(next).width>width&&line){lines.push(line);line=word;}else line=next;}
    if(line)lines.push(line);if(lines.length>maxLines)throw Error('Caption overflow: '+s);
    for(const [i,row] of lines.entries())text(ctx,row,x,y+i*(size+9),size);
  }
  function renderFrame(ctx,frame,spec,evidence,options={}){
    const m=frameModel(frame,spec,evidence,!!options.reducedMotion);
    ctx.fillStyle='#0b1119';ctx.fillRect(0,0,1920,1080);
    text(ctx,`OUTLIER ENGINEERING / 05 / ${m.scene.id}`,80,55,25,'#91a5b7');
    text(ctx,m.scene.chapter.toUpperCase(),80,118,56);
    text(ctx,m.disclosure,80,171,26,'#ffb54d');
    text(ctx,`${m.trace.inputs.workers} WORKERS / ${m.trace.inputs.tool_slots} SLOTS / ${(m.speed*(options.playbackRate??1)).toFixed(2)}x ${m.replay?'REPLAY':''}`,1050,171,28);
    for(const [s,x] of [['INPUT',95],['WORKERS',370],['TOOL QUEUE',740],['TOOL',1160],['DONE',1570]])text(ctx,s,x,235,30);
    // Playfield stays spatially stable; only the queue border and tiles shake.
    ctx.strokeStyle='#30495b';ctx.lineWidth=4;
    for(const [a,b,y] of [[270,345,420],[615,735,470],[1005,1140,515],[1425,1550,420]]){
      ctx.beginPath();ctx.moveTo(a,y);ctx.lineTo(b,y);ctx.lineTo(b-12,y-8);ctx.moveTo(b,y);ctx.lineTo(b-12,y+8);ctx.stroke();
    }
    ctx.save();ctx.translate(m.shake,0);ctx.strokeStyle='#b57b36';ctx.lineWidth=4;ctx.strokeRect(735,550,270,250);
    if(m.warningAlpha){ctx.fillStyle=`rgba(255,181,77,${m.warningAlpha})`;ctx.fillRect(735,550,270,250);}
    ctx.restore();
    text(ctx,`WAITING: ${m.counts.waiting}`,745,285,30,'#ffb54d');
    for(let w=0;w<m.trace.inputs.workers;w++){
      const job=m.rows.find(j=>j.worker===w&&['preparing','waiting','service'].includes(j.state));
      ctx.strokeStyle=job?C[job.state]:'#32485b';ctx.lineWidth=2;ctx.strokeRect(345,260+w*66,270,55);
      text(ctx,`W${w+1}`,358,298+w*66,25,'#91a5b7');
      if(job&&job.state!=='preparing')text(ctx,`holds J${job.id+1}`,425,298+w*66,25,C[job.state]);
      if(job&&job.state==='preparing'){ctx.fillStyle=C.preparing;ctx.fillRect(346,309+w*66,268*clamp((m.logicalMs-job.prep_start_ms)/m.trace.inputs.prep_ms,0,1),5);}
    }
    for(let s=0;s<m.trace.inputs.tool_slots;s++){
      const job=m.rows.find(j=>j.state==='service'&&j.slot===s);
      ctx.strokeStyle=job?'#eef4fb':'#785c35';ctx.strokeRect(1140,290+s*112,285,90);
      if(job){ctx.fillStyle=C.done;ctx.fillRect(1140,371+s*112,285*(m.logicalMs-job.service_start_ms)/m.trace.inputs.service_ms,9);}
      else text(ctx,'WAITING FOR JOB',1150,342+s*112,23,'#ffb54d');
    }
    const positions=[];
    for(const j of m.rows){
      ctx.globalAlpha=m.scene.id==='S04'&&j.id!==3?0.4:1;
      let [x,y]=tilePosition(j,m,spec);if(j.state==='waiting')x+=m.shake;
      positions.push({id:j.id,x,y,state:j.state});ctx.fillStyle=C[j.state];
      ctx.fillRect(x-spec.effects.physics.tile_width/2,y-spec.effects.physics.tile_height/2,spec.effects.physics.tile_width,spec.effects.physics.tile_height);text(ctx,`J${String(j.id+1).padStart(2,'0')}`,x-31,y+8,26,'#0b1119');
      if(j.state==='waiting')text(ctx,`${((m.logicalMs-j.prep_end_ms)/1000).toFixed(1)}s`,x-29,y+40,20,'#ffb54d');
    }
    ctx.globalAlpha=1;
    const count=m.counts;
    text(ctx,`IN ${count.input} + PREP ${count.preparing} + WAIT ${count.waiting} + TOOL ${count.service} + DONE ${count.done} = ${m.rows.length}`,80,830,29);
    text(ctx,`sim_time=${(m.logicalMs/1000).toFixed(2)}s  completed=${count.done}`,80,883,29,'#91a5b7');
    if(m.resultVisible)text(ctx,`TRACE RESULT: ${(m.trace.metrics.batch_ms/1000).toFixed(1)}s / peak queue ${m.trace.metrics.peak_tool_queue}`,870,883,28,C.done);
    if(m.scene.id==='S03'&&m.local>=15)text(ctx,`PREVIOUS RUN: ${(evidence.cases.underfed.metrics.batch_ms/1000).toFixed(1)}s`,80,925,27,'#ffb54d');
    if(m.egg)text(ctx,'EDITORIAL '+m.egg.text,80,927,25,'#91a5b7');
    // Captions are phrase-sized; never squeeze an entire scene into two lines.
    const sentences=m.cue.text.match(/[^.!?]+[.!?]?/g)||[];
    const p=clamp((m.local-m.cue.start)/(m.cue.end-m.cue.start),0,0.999);
    const caption=options.caption??sentences[Math.floor(p*sentences.length)]??'';
    wrapped(ctx,caption.trim(),80,980,1750,options.caption!==undefined?42:34,2);
    if(m.phase==='question'){
      text(ctx,'NEXT RUN: 4 -> 8',1030,55,30,'#ffb54d');
      text(ctx,'A: 2x SPEED?    B: TRAFFIC JAM?',750,925,33);
    }
    if(m.phase==='countdown'){
      ctx.fillStyle='rgba(6,12,20,0.94)';ctx.fillRect(520,215,880,675);
      text(ctx,'LOCK IN YOUR GUESS',590,300,58);
      text(ctx,String(m.countdown),835,660,310,'#ffb54d');
      const remain=(spec.challenge.reveal_start-m.time)/3;
      ctx.strokeStyle='#ffb54d';ctx.lineWidth=10;ctx.beginPath();ctx.arc(960,530,225,-Math.PI/2,-Math.PI/2+2*Math.PI*remain);ctx.stroke();
      text(ctx,'A: 2x SPEED?    B: TRAFFIC JAM?',595,825,35);
    }
    if(m.answerVisible)text(ctx,'TRAFFIC JAM. NOT A CRASH.',690,55,38,C.done);
    return {...m,positions};
  }
  return {states,frameModel,tilePosition,tickEvents,renderFrame};
});
