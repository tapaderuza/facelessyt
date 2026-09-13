import importlib.util
from pathlib import Path
import unittest

import yaml
try:
    from PIL import ImageChops
    PIL = True
except ImportError:
    PIL = False

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(PIL, 'Pillow is a video dependency')
class Episode04RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'production/04-local-memory/render_episode.py'
        spec = importlib.util.spec_from_file_location('episode04_renderer', path)
        cls.renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.renderer)
        cls.spec = yaml.safe_load((path.parent / 'episode.yaml').read_text(encoding='utf-8'))

    def test_narration_chunks_preserve_every_word(self):
        for scene in self.spec['scenes']:
            chunks = self.renderer.phrases(scene['narration'])
            self.assertEqual(' '.join(chunks).split(), scene['narration'].split())
            self.assertTrue(all(len(c) <= 100 for c in chunks))

    def test_budget_animation_uses_actual_calculator(self):
        r=self.renderer
        for scene,t,total in [('S01',0,9),('S01',4,6),('S06',12,9),('S07',6,7),('S08',6,9)]:
            self.assertEqual(r.scenario(scene,t)['total_budget_bytes']/r.GIB,total)

    def test_canvas_is_deterministic_and_geometry_moves(self):
        scene=self.spec['scenes'][5]
        a=self.renderer.artwork(scene,3)
        b=self.renderer.artwork(scene,7)
        self.assertEqual(a.tobytes(),self.renderer.artwork(scene,3).tobytes())
        self.assertIsNotNone(ImageChops.difference(a.crop((100,300,1800,900)),b.crop((100,300,1800,900))).getbbox())

    def test_layouts_and_caption_fit(self):
        for scene in self.spec['scenes']:
            for t in [0,*(beat[0]+1.5 for beat in scene['beats'])]:
                self.renderer.artwork(scene,t,'Measured subtitles remain inside the reserved area.')
            for phrase in self.renderer.phrases(scene['narration']):
                self.renderer.artwork(scene,0,phrase)

    def test_recap_has_motion_after_all_rows_revealed(self):
        scene=self.spec['scenes'][10]
        a=self.renderer.artwork(scene,20.1)
        b=self.renderer.artwork(scene,21.8)
        self.assertIsNotNone(ImageChops.difference(a,b).getbbox())

    def test_hook_keeps_red_result_during_spoken_conflict(self):
        scene=self.spec['scenes'][0]
        entry={'duration':26.,'cues':[{'text':'Watch the blue section:','start':8.,'end':10.},
                                    {'text':'a longer context pushes this example from six to nine.','start':10.,'end':13.}]}
        t=self.renderer.editorial_time(scene,entry,4.)
        self.assertEqual(self.renderer.scenario('S01',t)['status'],'over_budget')
        t=self.renderer.editorial_time(scene,entry,9.)
        self.assertEqual(self.renderer.scenario('S01',t)['total_budget_bytes']/self.renderer.GIB,6)

    def test_hook_supports_combined_measured_phrase(self):
        scene=self.spec['scenes'][0]
        entry={'duration':26.,'cues':[{'text':'Watch the blue section: a longer context pushes this example from six to nine.',
                                     'start':8.,'end':13.}]}
        t=self.renderer.editorial_time(scene,entry,4.)
        self.assertEqual(self.renderer.scenario('S01',t)['status'],'over_budget')
        self.assertGreater(self.renderer.editorial_time(scene,entry,12.),6)


if __name__=='__main__':unittest.main()
