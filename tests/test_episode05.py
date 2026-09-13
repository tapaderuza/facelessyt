"""Tests for Episode 5 preproduction. No claims about an unrendered MP4."""
import importlib.util
import json
from pathlib import Path
import unittest

PACKAGE = Path(__file__).resolve().parents[1]/'production/05-worker-bottleneck'
spec = importlib.util.spec_from_file_location('episode05_simulation', PACKAGE/'simulate.py')
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)


class Episode05Tests(unittest.TestCase):
    def test_four_expected_results(self):
        expected = {'underfed': (15000, 0), 'baseline': (12500, 2),
                    'double_workers': (12500, 6), 'double_capacity': (6500, 4)}
        for name, trace in sim.cases().items():
            self.assertEqual((trace['metrics']['batch_ms'], trace['metrics']['peak_tool_queue']), expected[name])

    def test_deterministic_replay(self):
        self.assertEqual(sim.cases(), sim.cases())

    def test_conservation_and_resource_limits_at_events(self):
        for workers in (1, 2, 4, 8, 20):
            for slots in (1, 2, 4):
                trace = sim.simulate(workers=workers, tool_slots=slots)
                times = {0, trace['metrics']['batch_ms']}
                for event in trace['events']:
                    times.update((max(0, event['t_ms']-0.1), event['t_ms'], event['t_ms']+0.1))
                for t in times:
                    state = sim.state_at(trace, t)
                    ids = sum(state.values(), [])
                    self.assertEqual(sorted(ids), list(range(12)))
                    self.assertLessEqual(len(state['service']), slots)
                    occupied = state['preparing']+state['waiting']+state['service']
                    self.assertLessEqual(len(occupied), workers)
                    self.assertEqual(len({trace['jobs'][j]['worker'] for j in occupied}), len(occupied))

    def test_fifo_and_latency_accounting(self):
        for trace in sim.cases().values():
            ready = sorted(trace['jobs'], key=lambda j: (j['prep_end_ms'], j['id']))
            started = sorted(trace['jobs'], key=lambda j: (j['service_start_ms'], j['id']))
            self.assertEqual([j['id'] for j in ready], [j['id'] for j in started])
            for j in trace['jobs']:
                self.assertEqual(j['end_to_end_ms'], j['input_wait_ms']+trace['inputs']['prep_ms']+
                                 j['tool_wait_ms']+trace['inputs']['service_ms'])

    def test_doubling_workers_moves_wait_not_completion_times(self):
        a, b = sim.simulate(workers=4), sim.simulate(workers=8)
        self.assertEqual([j['complete_ms'] for j in a['jobs']], [j['complete_ms'] for j in b['jobs']])
        self.assertLess(sum(j['tool_wait_ms'] for j in a['jobs']), sum(j['tool_wait_ms'] for j in b['jobs']))

    def test_invalid_inputs(self):
        for value in (0, -1, True, 2.5, float('nan')):
            with self.assertRaises(ValueError):
                sim.simulate(workers=value)
        for value in (-1, True, float('inf'), float('nan')):
            with self.assertRaises(ValueError):
                sim.state_at(sim.simulate(), value)

    def test_saved_evidence_matches_executable(self):
        saved = json.loads((PACKAGE/'simulation-evidence.json').read_text(encoding='utf-8'))
        for trace in saved['cases'].values():
            self.assertEqual(trace, sim.simulate(**trace['inputs']))

    def test_full_four_minute_plan_and_three_second_contract(self):
        plan = json.loads((PACKAGE/'render-spec.json').read_text(encoding='utf-8'))
        cursor = 0
        for scene in plan['scenes']:
            self.assertEqual(scene['start'], cursor)
            frames = [b['frame'] for b in scene['target_beats']]+[scene['end']*plan['fps']]
            self.assertEqual(frames[0], cursor*plan['fps'])
            self.assertTrue(all(0 < b-a <= 90 for a, b in zip(frames, frames[1:])))
            cursor = scene['end']
        self.assertEqual(cursor, 240)
        self.assertTrue(plan['render_contract']['renderer_implemented'])
        self.assertFalse(plan['render_contract']['measured_voice_integrated'])
        self.assertTrue(plan['render_contract']['motion']['decorative_pulses_do_not_satisfy_hold_gate'])

    def test_prediction_pause_and_single_correct_answer(self):
        plan = json.loads((PACKAGE/'render-spec.json').read_text(encoding='utf-8'))
        c = plan['challenge']
        self.assertEqual((c['reveal_start']-c['pause_start'])*plan['fps'], 90)
        self.assertEqual(c['question_start']/plan['target_seconds'], 0.5)
        self.assertEqual(c['correct'], 'B')
        self.assertIn('12.5', c['answer'])

    def test_every_spoken_cue_has_a_visual_and_countdown_has_no_voice(self):
        plan = json.loads((PACKAGE/'render-spec.json').read_text(encoding='utf-8'))
        countdowns = []
        for scene in plan['scenes']:
            cursor = 0
            for cue in scene['cues']:
                self.assertEqual(cue['start'], cursor)
                self.assertTrue(cue['visual'])
                if cue.get('countdown'):
                    countdowns.append(cue)
                    self.assertEqual(cue['text'], '')
                else:
                    self.assertTrue(cue['text'])
                cursor = cue['end']
            self.assertEqual(cursor, 30)
        self.assertEqual(len(countdowns), 1)
        self.assertEqual(countdowns[0]['end']-countdowns[0]['start'], 3)

    def test_effects_are_bounded_and_jokes_are_editorial(self):
        plan = json.loads((PACKAGE/'render-spec.json').read_text(encoding='utf-8'))
        self.assertLessEqual(plan['effects']['shake']['max_px'], 3)
        self.assertFalse(plan['effects']['warning']['full_screen_flash'])
        self.assertGreaterEqual(plan['effects']['warning']['pulse_period_s'], 2)
        evidence = (PACKAGE/'simulation-evidence.json').read_text(encoding='utf-8')
        for egg in plan['easter_eggs']:
            self.assertEqual(egg['kind'], 'editorial_joke')
            self.assertNotIn(egg['text'], evidence)

    def test_selection_is_not_fabricated_demand(self):
        report = json.loads((PACKAGE/'selection-evidence.json').read_text(encoding='utf-8'))
        self.assertIsNone(report['automatic_selection'])
        self.assertIsNone(report['direct_demand_evidence_for_selected_angle'])
        self.assertFalse(report['adjacent_cluster']['eligible'])
        self.assertNotIn(report['selected_angle'], report['excluded_episode_keys'])


if __name__ == '__main__':
    unittest.main()
