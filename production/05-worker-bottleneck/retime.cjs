/* Measured audio time -> authored visual time, with an exact 90-frame pause. */
function locate(frame,timeline){
  if(!Number.isInteger(frame)||frame<0||frame>=timeline.frames)throw Error('production frame out of range');
  const entry=timeline.scenes.find(s=>frame>=s.start_frame&&frame<s.start_frame+s.frames);
  const local=frame-entry.start_frame;
  const unit=entry.units.find(u=>local>=u.start_frame&&local<u.end_frame);
  if(!unit)throw Error('Missing measured unit');
  const progress=(local-unit.start_frame)/(unit.end_frame-unit.start_frame);
  const editorial=unit.editorial_start+progress*(unit.editorial_end-unit.editorial_start);
  const actualTime=local/timeline.fps;
  const caption=entry.cues.find(c=>actualTime>=c.start&&actualTime<c.end)?.text||'';
  return {entry,unit,editorial,editorialFrame:Math.floor(editorial*timeline.fps+1e-7),caption,
    playbackRate:(unit.editorial_end-unit.editorial_start)/((unit.end_frame-unit.start_frame)/timeline.fps)};
}
module.exports={locate};
