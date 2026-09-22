"""Reglas de gancho, ritmo y packaging (2026-09-18). Sin red, sin ffmpeg, sin TTS.

Ejecutar:  .venv/Scripts/python.exe -m unittest tests.test_retention_rules -v
"""

from __future__ import annotations

import json
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
        self.assertEqual(
            packaging.lint_title("8 Workers, Same Speed: Where the Queue Actually Went"), [])

    def test_titulo_demasiado_corto(self):
        """Los outliers del nicho estan en 58 caracteres; <50 puntua 3,3x."""
        problems = packaging.lint_title("180 Views. The Fix Was a Linter.")
        self.assertTrue(any("caracteres" in p for p in problems), problems)

    def test_herramienta_en_el_titulo(self):
        self.assertEqual(packaging.names_tool("Claude Code Hooks: My Agent Can't Skip It"),
                         "claude code")
        self.assertEqual(packaging.names_tool("My Retry Loop Paid ElevenLabs Twice"), "elevenlabs")
        self.assertIsNone(packaging.names_tool("180 Views in 28 Days. The Fix Was a Linter."))
        # 'claudette' no es 'claude': la frontera de palabra importa.
        self.assertIsNone(packaging.names_tool("Claudette and the gptx problem"))

    def test_nota_de_busqueda(self):
        self.assertIn("claude code", packaging.title_search_note("Claude Code Hooks in 40 Lines"))
        self.assertIn("no nombra", packaging.title_search_note("A Linter For My Scripts"))

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


    def test_imagen_externa_con_banda(self):
        """Fondo tipo DALL-E + banda de color puesta por codigo.

        La banda sube luminancia y saturacion, pero NO salva una imagen negra:
        si el fondo es negro puro, el gate la sigue rechazando, que es lo que
        queremos (es exactamente lo que fallo en los episodios 1-4).
        """
        from PIL import Image
        from facelessyt.video import thumbnail
        with tempfile.TemporaryDirectory() as tmp:
            black = Path(tmp) / "black.png"
            Image.new("RGB", (1024, 1024), (12, 14, 20)).save(black)
            out = thumbnail.render_over_image(black, Path(tmp) / "t1.jpg",
                                              headline="Same speed with 8 workers", figure="2x")
            self.assertFalse(packaging.audit_thumbnail(out).ok)

            navy = Path(tmp) / "navy.png"  # oscuro pero con algo de luz, como una foto de estudio
            Image.new("RGB", (1024, 1024), (48, 56, 72)).save(navy)
            out = thumbnail.render_over_image(navy, Path(tmp) / "t2.jpg",
                                              headline="Same speed with 8 workers", figure="2x")
            audit = packaging.audit_thumbnail(out)
            self.assertTrue(audit.ok, audit.problems)
            self.assertEqual((audit.width, audit.height), (1280, 720))


class RevealTests(unittest.TestCase):
    def test_pasos_igual_a_lineas_con_texto(self):
        from facelessyt.video import scenes
        scene = {"id": "x", "visual": {"type": "terminal", "content": "rule_card"}}
        self.assertGreater(scenes.reveal_steps(scene), 1)

    def test_texto_centrado_no_se_revela(self):
        from facelessyt.video import scenes
        scene = {"id": "x", "visual": {"type": "text", "content": "Something"}}
        self.assertEqual(scenes.reveal_steps(scene), 1)

    def test_reveal_false_lo_desactiva(self):
        from facelessyt.video import scenes
        scene = {"id": "x", "visual": {"type": "terminal", "content": "rule_card"}, "reveal": False}
        self.assertEqual(scenes.reveal_steps(scene), 1)

    def test_la_geometria_no_salta_entre_pasos(self):
        """Cada paso solo añade texto: ningun pixel dibujado se mueve."""
        from PIL import Image, ImageChops
        from facelessyt.video import scenes
        scene = {"id": "x", "visual": {"type": "terminal", "content": "exit_codes"}}
        with tempfile.TemporaryDirectory() as tmp:
            pngs = scenes.render_reveal(scene, Path(tmp), "x")
            self.assertGreater(len(pngs), 2)
            full = Image.open(pngs[-1]).convert("RGB")
            for png in pngs[:-1]:
                step = Image.open(png).convert("RGB")
                # Lo que el paso dibuja tiene que ser identico en la imagen final.
                diff = ImageChops.difference(step, full)
                lighter = ImageChops.difference(step, ImageChops.darker(step, full))
                self.assertIsNone(lighter.getbbox(),
                                  f"{png.name} dibuja algo que no esta en la imagen final")
                self.assertIsNotNone(diff.getbbox(), f"{png.name} no añade nada")

    def test_listing_de_concat_repite_el_ultimo(self):
        from facelessyt.video import assemble
        with tempfile.TemporaryDirectory() as tmp:
            pngs = [Path(tmp) / f"{i}.png" for i in range(3)]
            for p in pngs:
                p.write_bytes(b"")
            listing = assemble.reveal_listing(pngs, Path(tmp) / "seq.txt", duration=6.0, hold=0.5)
            rows = listing.read_text(encoding="utf-8").splitlines()
            files = [r for r in rows if r.startswith("file ")]
            # un paso por PNG, mas el ultimo con el resto de la duracion, mas
            # la repeticion final que el demuxer de concat necesita.
            self.assertEqual(len(files), len(pngs) + 2)
            self.assertEqual(files[-1], files[-2])
            self.assertEqual(files[-1], files[len(pngs) - 1])
            per = [float(r.split()[1]) for r in rows if r.startswith("duration")]
            self.assertAlmostEqual(per[0], 6.0 * assemble.REVEAL_SHARE / 3, places=3)
            # El listado dura de mas a proposito: `-t` corta en el montaje.
            self.assertAlmostEqual(sum(per), 6.0 + 0.5 + assemble.REVEAL_TAIL_MARGIN, places=2)
            self.assertGreater(sum(per), 6.0 + 0.5)


class VoiceGuardTests(unittest.TestCase):
    """Re-locutar un episodio con otro motor tiene que doler.

    Regresion del 2026-09-22: un `docker run` sin las variables de ElevenLabs
    hizo que `--engine auto` cayera a Piper y el episodio 8 se volviera a
    locutar entero con otra voz, sin un solo aviso.
    """

    def _workdir(self, tmp: str, engine_key: str) -> Path:
        wd = Path(tmp) / "ep"
        (wd / "audio").mkdir(parents=True)
        (wd / "audio" / "hook-1.key.json").write_text(
            json.dumps({"key": f"{engine_key}|voz|texto", "path": "x.mp3"}), encoding="utf-8")
        return wd

    def test_cambio_de_motor_revienta(self):
        from facelessyt.video import assemble
        with tempfile.TemporaryDirectory() as tmp:
            wd = self._workdir(tmp, "elevenlabs")
            with self.assertRaises(assemble.VoiceChangeError) as ctx:
                assemble.check_engine(wd, "piper")
            self.assertIn("ELEVENLABS_API_KEY", str(ctx.exception))

    def test_mismo_motor_pasa(self):
        from facelessyt.video import assemble
        with tempfile.TemporaryDirectory() as tmp:
            wd = self._workdir(tmp, "piper")
            self.assertEqual(assemble.check_engine(wd, "piper"), "piper")

    def test_episodio_nuevo_pasa(self):
        from facelessyt.video import assemble
        with tempfile.TemporaryDirectory() as tmp:
            wd = Path(tmp) / "nuevo"
            wd.mkdir()
            self.assertEqual(assemble.check_engine(wd, "piper"), "piper")
            self.assertIsNone(assemble.cached_engine(wd))

    def test_allow_change_lo_permite(self):
        from facelessyt.video import assemble
        with tempfile.TemporaryDirectory() as tmp:
            wd = self._workdir(tmp, "elevenlabs")
            self.assertEqual(assemble.check_engine(wd, "piper", allow_change=True), "piper")


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


class PaidCacheTests(unittest.TestCase):
    def test_paga_una_vez_y_reutiliza(self):
        from facelessyt import paidcache
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "a.mp3"

            def produce():
                calls.append(1)
                out.write_bytes(b"audio")
                return out

            marker = Path(tmp) / "a.key.json"
            self.assertEqual(paidcache.once(marker, "voiceA|hello", produce), out)
            self.assertEqual(paidcache.once(marker, "voiceA|hello", produce), out)
            self.assertEqual(len(calls), 1)
            # Otra voz con el mismo texto: se vuelve a pagar. Ese era el fallo.
            paidcache.once(marker, "voiceB|hello", produce)
            self.assertEqual(len(calls), 2)
            # Fichero borrado: se regenera aunque la clave coincida.
            out.unlink()
            paidcache.once(marker, "voiceB|hello", produce)
            self.assertEqual(len(calls), 3)

    def test_fingerprint_cambia_con_la_voz(self):
        import os
        from facelessyt.video import voice
        before = dict(os.environ)
        try:
            os.environ["ELEVENLABS_API_KEY"] = "k"
            os.environ["ELEVENLABS_VOICE_ID"] = "v1"
            a = voice.fingerprint("auto")
            os.environ["ELEVENLABS_VOICE_ID"] = "v2"
            b = voice.fingerprint("auto")
            self.assertNotEqual(a, b)
            self.assertTrue(a.startswith("elevenlabs|v1|"))
            self.assertTrue(voice.fingerprint("piper").startswith("piper|"))
        finally:
            os.environ.clear(); os.environ.update(before)


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
