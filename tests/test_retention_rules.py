"""Reglas de gancho, ritmo y packaging (2026-09-18). Sin red, sin ffmpeg, sin TTS.

Ejecutar:  .venv/Scripts/python.exe -m unittest tests.test_retention_rules -v
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from facelessyt import packaging
from facelessyt.video import assemble, lint


def scene(sid: str, words: int, content: str = "x", **extra) -> dict:
    return {"id": sid, "narration": " ".join(["word"] * words),
            "visual": {"type": "text", "content": content}, **extra}


def good_script(n_scenes: int = 10) -> dict:
    scenes = [
        {"id": "hook-1", "narration": "Watch this: 8 workers, same 12.5 seconds.",
         "visual": {"type": "text", "content": "a"}},
        {"id": "hook-2", "narration": "The queue moved. It did not shrink.",
         "visual": {"type": "text", "content": "b"}},
        {"id": "hook-3", "narration": "Here is where it went.",
         "visual": {"type": "text", "content": "c"}},
    ]
    scenes += [scene(f"body-{i}", 40, content=f"v{i}") for i in range(n_scenes)]
    return {"video": {"id": "t"}, "scenes": scenes}


class LintGanchoTests(unittest.TestCase):
    def rules(self, spec):
        return {i.rule for i in lint.lint_script(spec) if i.level == "error"}

    def test_guion_correcto_pasa(self):
        self.assertEqual(lint.lint_script(good_script()), [])

    def test_primera_escena_larga(self):
        spec = good_script()
        spec["scenes"][0]["narration"] = "you " + " ".join(["word"] * 31)
        self.assertIn("hook-length", self.rules(spec))

    def test_primera_escena_sin_payoff(self):
        spec = good_script()
        spec["scenes"][0]["narration"] = "Everyone obsesses over editing and thumbnails."
        self.assertIn("hook-payoff", self.rules(spec))

    def test_hablar_del_canal_en_el_gancho(self):
        """Lo que abria el video 1: 'This channel has zero videos and zero subscribers'."""
        spec = good_script()
        spec["scenes"][0]["narration"] = "This channel has 0 videos and 0 subscribers."
        self.assertIn("hook-self-talk", self.rules(spec))

    def test_last_video_en_segunda_escena(self):
        spec = good_script()
        spec["scenes"][1]["narration"] = "Last video I built a tool that finds topics."
        self.assertIn("hook-self-talk", self.rules(spec))

    def test_gancho_estatico(self):
        """Tres escenas que llenan los primeros 30 s sobre la misma imagen."""
        spec = good_script()
        spec["scenes"][1]["narration"] = " ".join(["word"] * 40)
        spec["scenes"][2]["narration"] = " ".join(["word"] * 40)
        for s in spec["scenes"][:3]:
            s["visual"]["content"] = "same"
        self.assertIn("hook-static", self.rules(spec))

    def test_escena_demasiado_larga(self):
        spec = good_script()
        spec["scenes"].append(scene("long", lint.SCENE_MAX_WORDS + 1, content="z"))
        self.assertIn("scene-too-long", self.rules(spec))

    def test_mismo_visual_dos_veces_avisa(self):
        spec = good_script()
        spec["scenes"] += [scene("a1", 40, content="dup"), scene("a2", 40, content="dup")]
        warns = {i.rule for i in lint.lint_script(spec) if i.level == "warn"}
        self.assertIn("same-visual-twice", warns)

    def test_demasiado_largo_salvo_allow_long(self):
        spec = good_script(n_scenes=45)  # ~9,5 min a 190 wpm
        self.assertIn("too-long", self.rules(spec))
        spec["video"]["allow_long"] = True
        self.assertNotIn("too-long", self.rules(spec))
        del spec["video"]["allow_long"]
        spec["video"]["max_minutes"] = 12
        self.assertNotIn("too-long", self.rules(spec))

    def test_guion_del_video_1_no_pasa(self):
        """Regresion sobre el gancho real del episodio 1."""
        spec = {"video": {"id": "01"}, "scenes": [
            {"id": "hook-1", "visual": {"type": "terminal", "content": "empty_studio"},
             "narration": "This channel has zero videos and zero subscribers. But I already "
                          "know exactly which four videos I'm making next. And I didn't guess."},
            {"id": "hook-2", "visual": {"type": "text", "content": "12.7x"},
             "narration": "I didn't use my gut. I didn't pay for a keyword tool. I built something that told me."},
        ]}
        self.assertTrue({"hook-self-talk", "hook-payoff"} <= self.rules(spec))


class PackagingTests(unittest.TestCase):
    def test_texto_miniatura_pronombre(self):
        for text in ("IT LIED", "IT FITS?", "IT'S A TRAP", "I FOUND IT"):
            self.assertTrue(packaging.lint_thumb_text(text), text)

    def test_texto_miniatura_con_referente(self):
        self.assertEqual(packaging.lint_thumb_text("2x WORKERS SAME SPEED"), [])
        self.assertEqual(packaging.lint_thumb_text("12.7x"), [])

    def test_texto_miniatura_repite_titulo(self):
        problems = packaging.lint_thumb_text("Doubled Workers", "I Doubled the Workers")
        self.assertTrue(any("repite el titulo" in p for p in problems))

    def test_titulo_largo_y_repetido(self):
        self.assertTrue(packaging.lint_title("x" * 61))
        self.assertTrue(packaging.lint_title("I Built an AI Agent That Does Things"))
        self.assertEqual(packaging.lint_title("8 Workers, Same Speed: Where the Queue Went"), [])

    def test_audit_rechaza_miniatura_negra(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            dark = Path(tmp) / "dark.png"
            img = Image.new("RGB", (1280, 720), (10, 12, 16))
            img.paste((240, 240, 240), (40, 300, 500, 420))  # texto blanco pequeno
            img.save(dark)
            audit = packaging.audit_thumbnail(dark)
            self.assertFalse(audit.ok)
            self.assertGreater(audit.dark_share, packaging.THUMB_MAX_DARK_SHARE)

    def test_audit_acepta_render_bold(self):
        from facelessyt.video import thumbnail
        with tempfile.TemporaryDirectory() as tmp:
            out = thumbnail.render_bold(Path(tmp) / "t.jpg", headline="Same speed with 8 workers",
                                        figure="2x", sub="the queue moved")
            audit = packaging.audit_thumbnail(out)
            self.assertTrue(audit.ok, audit.problems)
            self.assertEqual((audit.width, audit.height), (1280, 720))


    def test_audit_acepta_imagen_externa_con_banda(self):
        """Fondo oscuro tipo DALL-E + banda de color puesta por codigo."""
        from PIL import Image
        from facelessyt.video import thumbnail
        with tempfile.TemporaryDirectory() as tmp:
            bg = Path(tmp) / "bg.png"
            Image.new("RGB", (1024, 1024), (12, 14, 20)).save(bg)  # cuadrada y negra
            out = thumbnail.render_over_image(bg, Path(tmp) / "t.jpg",
                                              headline="Same speed with 8 workers", figure="2x")
            audit = packaging.audit_thumbnail(out)
            self.assertTrue(audit.ok, audit.problems)
            self.assertEqual((audit.width, audit.height), (1280, 720))


class AssembleTests(unittest.TestCase):
    def test_motion_filter_alterna_direccion(self):
        f0 = assemble.motion_filter(10.0, 0)
        f1 = assemble.motion_filter(10.0, 1)
        self.assertIn("min(1+", f0)
        self.assertIn(f"max({assemble.ZOOM_MAX}-", f1)
        self.assertIn("d=300", f0)  # 10 s * 30 fps
        self.assertIn("s=1920x1080", f0)

    def test_capitulos_descuentan_el_fundido(self):
        clips = [assemble.Clip("a", Path("a.mp4"), 10.0, 1),
                 assemble.Clip("b", Path("b.mp4"), 10.0, 1),
                 assemble.Clip("c", Path("c.mp4"), 10.0, 1)]
        spec = [{"id": "a", "chapter": "A"}, {"id": "b"}, {"id": "c", "chapter": "C"}]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ch.txt"
            assemble.write_chapters(clips, spec, out, transitions=True)
            lines = out.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines, ["00:00 A", "00:19 C"])  # 20 s menos 2 fundidos de 0,25
            assemble.write_chapters(clips, spec, out, transitions=False)
            self.assertEqual(out.read_text(encoding="utf-8").splitlines(), ["00:00 A", "00:20 C"])


class PublishAtTests(unittest.TestCase):
    def test_futuro_en_utc(self):
        from facelessyt import upload
        future = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M+00:00")
        dt = upload.parse_publish_at(future)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_pasado_rechazado(self):
        from facelessyt import upload
        with self.assertRaises(ValueError):
            upload.parse_publish_at("2020-01-01T10:00")


if __name__ == "__main__":
    unittest.main()
