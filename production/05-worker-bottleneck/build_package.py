"""Build gamified Episode 5 artifacts offline. No voice, MP4 or upload."""
import hashlib
import json
from pathlib import Path
import re
import yaml
from simulate import cases, simulate

PACKAGE = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def words(text):
    return len(re.findall(r"\b[\w]+(?:['.-][\w]+)*\b", text))

def validate(episode):
    assert episode['status'] == 'preproduction_only'
    assert episode['target_seconds'] == 240
    assert episode['timing']['max_semantic_hold_seconds'] == 3
    assert episode['timing']['challenge_pause_seconds'] == 3
    report, cursor = [], 0
    for scene in episode['scenes']:
        assert scene['start'] == cursor
        assert scene['end']-scene['start'] == 30
        assert len(scene['beats']) == 12
        cue_cursor = 0
        for cue in scene['cues']:
            assert cue['start'] == cue_cursor and cue['end'] > cue['start']
            assert cue['visual'], 'Every line needs a visible action'
            if cue.get('countdown'):
                assert not cue['text'] and cue['end']-cue['start'] == 3
            else:
                assert cue['text']
                assert words(cue['text'])*60/(cue['end']-cue['start']) <= 250
            cue_cursor = cue['end']
        assert cue_cursor == 30
        scene['narration'] = ' '.join(c['text'] if not c.get('countdown') else '[COUNTDOWN_3_SECONDS]' for c in scene['cues'])
        count = sum(words(c['text']) for c in scene['cues'])
        voice_seconds = 27 if scene['playback'].get('challenge') else 30
        report.append({'scene': scene['id'], 'words': count, 'target_wpm': round(count*60/voice_seconds, 1),
                       'scheduled_max_beat_gap_s': 2.5, 'all_cues_have_visual_actions': True})
        cursor = scene['end']
    assert cursor == episode['target_seconds']
    c = episode['challenge']
    assert c['reveal_start']-c['pause_start'] == 3
    assert c['question_start']/cursor == 0.5
    assert c['answer_highlight_not_before'] == c['trace_run_video_end']
    assert (c['trace_run_video_end']-c['trace_run_video_start'])*c['trace_speed'] == 12.5
    challenge_scene = next(s for s in episode['scenes'] if s['id'] == c['scene'])
    assert challenge_scene['cues'][0]['text'] == c['question']
    assert sum(cue.get('countdown', False) for s in episode['scenes'] for cue in s['cues']) == 1
    assert episode['effects']['shake']['max_px'] <= 3
    assert not episode['effects']['warning']['full_screen_flash']
    for egg in episode['easter_eggs']:
        assert egg['kind'] == 'editorial_joke' and egg['text'].startswith('//')
        assert 0 <= egg['at'] < egg['until'] <= 30
    return report

def main():
    episode = yaml.safe_load((PACKAGE/'episode.yaml').read_text(encoding='utf-8'))
    scene_qa = validate(episode)
    results = cases()
    results['longer_preparation'] = simulate(prep_ms=3000)
    results['slower_tool'] = simulate(service_ms=3000)
    results['larger_burst'] = simulate(jobs=16)
    evidence = {'disclosure': episode['disclosure'], 'simulation_source_sha256': digest(PACKAGE/'simulate.py'), 'cases': results}
    # Selection is historical evidence, not something a retention rewrite can improve.
    selection = json.loads((PACKAGE/'selection-evidence.json').read_text(encoding='utf-8'))
    assert selection['selected_angle'] == episode['topic_key']
    episode['render_contract'] = {
        'version': 'oe.gamified-canvas.v2',
        'renderer_implemented': True,
        'implementation_scope': 'deterministic full visual timeline and interactive preview, not voiced final MP4',
        'renderer': 'renderer.js',
        'required_interface': 'renderFrame(ctx, integerFrame, spec, evidence, {reducedMotion})',
        'measured_voice_integrated': False,
        'caption_timing': 'sentence subdivision inside editorial cue targets; replace with measured phrases before final production',
        'determinism': 'Pure frame index plus stored traces. Analytic gravity and damped impact; no random or accumulated wall-clock physics.',
        'truth_boundary': 'Gravity, stack impact, shake and comments are presentation. Numeric metrics and job conservation remain exclusively trace-derived.',
        'semantic_hold_gate': 'Sliding 90-frame windows in technical ROI; ignore logos/captions/camera shake/warning pulses. During the exact 90-frame frozen prediction interval, the countdown is the explicit interaction. Verify again on encoded MP4 after voice retiming.',
        'challenge_gate': '90 frames: 3, 2, 1. Frozen state, neutral choices, no results or verdict. Three quiet ticks; zero voice. Resume from t=0, reveal verdict only after trace completion.',
        'motion': {'decorative_pulses_do_not_satisfy_hold_gate': True, 'gravity_from_spec': True, 'no_unbounded_shake': True},
        'easter_egg_gate': 'Editorial comments in separate display field; never inject into evidence, executable simulation output or error status.',
        'audio': {'target_lufs': -16, 'true_peak_ceiling_dbtp': -1.5, 'voice_during_countdown': False,
                  'tick_frames': [(episode['challenge']['pause_start']+i)*episode['fps'] for i in range(3)],
                  'tick_duration_ms': 70, 'tick_gain': 0.025},
        'release_gate': ['all unit/state/render tests', 'measured voice anchors', 'encoded motion and flash review',
                         'full audiovisual review', 'mobile readability', 'verified chapters and source links',
                         'explicit public upload authorization'],
    }
    for scene in episode['scenes']:
        scene['target_beats'] = [{'frame': round((scene['start']+i*2.5)*episode['fps']), 'event': text}
                                 for i, text in enumerate(scene['beats'])]
    guion = ['# Episodio 05 — '+episode['title'], '', '## Revisión gamificada: 4:00 objetivo', '',
             'Locución en inglés. Cada frase tiene una acción visual. Tiempos editoriales, no voz medida.',
             'Cuenta atrás: 3 segundos, tres ticks discretos, sin narración; no se presenta un atasco como caída real.', '']
    for scene in episode['scenes']:
        t = scene['start']
        guion += [f"## {t//60:02}:{t%60:02} — {scene['chapter']} ({scene['id']})", '', scene['layout'], '']
        for cue in scene['cues']:
            a, b = t+cue['start'], t+cue['end']
            guion += [f"### {a//60:02}:{a%60:02}–{b//60:02}:{b%60:02}", '',
                      cue['text'] or '**[3 → 2 → 1: sin voz, tres ticks, simulación congelada]**', '',
                      'En pantalla: '+cue['visual']+'.', '']
    guion += ['## Easter eggs — comentarios editoriales, no errores reales', '']
    for egg in episode['easter_eggs']:
        guion += [f"- {egg['scene']} +{egg['at']}–{egg['until']} s: `{egg['text']}`"]
    (PACKAGE/'GUION.md').write_text('\n'.join(guion)+'\n', encoding='utf-8')
    for name, value in [('render-spec.json', episode), ('simulation-evidence.json', evidence)]:
        (PACKAGE/name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    template = (PACKAGE/'lab-template.html').read_text(encoding='utf-8')
    template = template.replace('__EVIDENCE_JSON__', json.dumps(evidence).replace('<', '\\u003c'))
    template = template.replace('__SPEC_JSON__', json.dumps(episode).replace('<', '\\u003c'))
    template = template.replace('__RENDERER_JS__', (PACKAGE/'renderer.js').read_text(encoding='utf-8'))
    (PACKAGE/'lab.html').write_text(template, encoding='utf-8')
    qa = {'status': 'preproduction_structure_pass_not_final_video_qa', 'scenes': scene_qa,
          'total_words': sum(s['words'] for s in scene_qa), 'target_seconds': episode['target_seconds'],
          'scheduled_beats': sum(len(s['beats']) for s in episode['scenes']),
          'challenge_countdown_frames': 90, 'voice_during_countdown': False,
          'actual_voice_measured': False, 'encoded_motion_verified': False, 'public_upload': False,
          'source_sha256': digest(PACKAGE/'episode.yaml'), 'simulation_sha256': digest(PACKAGE/'simulate.py'),
          'renderer_sha256': digest(PACKAGE/'renderer.js')}
    (PACKAGE/'preproduction-qa.json').write_text(json.dumps(qa, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(qa, indent=2))

if __name__ == '__main__':
    main()
