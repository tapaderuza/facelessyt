"""Genera el video a partir del guion.

  python -m facelessyt.video check  --script ...                        (lint, sin render)
  python -m facelessyt.video render --script scripts/01-outlier-agent.yaml
  python -m facelessyt.video render --script ... --only hook-1,hook-2   (prueba rapida)
  python -m facelessyt.video render --script ... --music /path/loop.mp3

`render` ejecuta el mismo lint que `check` y se niega a renderizar un guion
con errores de gancho o ritmo: son los que la retencion ya ha castigado.
`--force` salta ese bloqueo cuando sabes lo que haces.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml

from . import assemble, lint, scenes


def load_script(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _lint_report(spec: dict) -> list[lint.Issue]:
    issues = lint.lint_script(spec)
    scene_list = spec["scenes"]
    words = sum(len(s.get("narration", "").split()) for s in scene_list)
    print(f"Escenas      : {len(scene_list)}")
    print(f"Palabras     : {words}")
    print(f"Duracion est.: {lint.estimate_minutes(scene_list):.1f} min "
          f"(objetivo {spec['video'].get('target_minutes')}, "
          f"maximo {spec['video'].get('max_minutes', lint.MAX_MINUTES_DEFAULT)})")
    if issues:
        errors = sum(i.level == "error" for i in issues)
        print(f"\n{len(issues)} aviso(s), {errors} error(es) de gancho/ritmo:")
        for issue in issues:
            print(issue)
    return issues


def cmd_check(args: argparse.Namespace) -> int:
    """Valida el guion sin generar nada: visuales, y reglas de gancho y ritmo."""
    spec = load_script(Path(args.script))
    problems = []
    for scene in spec["scenes"]:
        key = scene.get("visual", {}).get("content", "")
        if key not in scenes.CONTENT and scene.get("visual", {}).get("type") != "text":
            problems.append(f"  {scene['id']}: no hay visual para '{key}'")
        if not scene.get("narration", "").strip():
            problems.append(f"  {scene['id']}: sin narracion")

    issues = _lint_report(spec)

    if problems:
        print(f"\n{len(problems)} problema(s) de render:")
        print("\n".join(problems))
    if problems or lint.has_errors(issues):
        return 1
    print("\nOK: todas las escenas se pueden renderizar y el guion pasa el lint")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    spec = load_script(Path(args.script))
    video_id = spec["video"]["id"]
    scene_list = spec["scenes"]

    if not args.only:
        issues = _lint_report(spec)
        if lint.has_errors(issues) and not args.force:
            print("\nNo se renderiza: arregla los errores o usa --force.")
            return 1
        print()

    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        scene_list = [s for s in scene_list if s["id"] in wanted]
        if not scene_list:
            print(f"Ninguna escena coincide con: {args.only}")
            return 1

    workdir = Path(args.workdir or f"data/video/{video_id}")
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        engine = assemble.check_engine(workdir, args.engine,
                                       allow_change=args.allow_voice_change)
    except assemble.VoiceChangeError as exc:
        print(f"\nNo se renderiza: {exc}")
        return 3
    print(f"Voz           : {engine}")
    motion = not args.no_motion
    transitions = not args.no_transitions
    reveal = not args.no_reveal

    clips, started = [], time.time()
    for i, scene in enumerate(scene_list):
        print(f"[{i + 1:2}/{len(scene_list)}] {scene['id']:24}", end=" ", flush=True)
        try:
            clip = assemble.build_scene(scene, workdir, engine=engine,
                                        index=i, motion=motion, reveal=reveal)
        except (scenes.SceneError, assemble.AssembleError) as exc:
            print("FALLO")
            print(f"\n{exc}")
            return 2
        clips.append(clip)
        print(f"{clip.duration:5.1f}s  ({clip.words} palabras)")

    out = Path(args.out or f"data/video/{video_id}.mp4")
    music = Path(args.music) if args.music else None
    try:
        assemble.concat(clips, out, workdir, transitions=transitions, music=music)
    except assemble.AssembleError as exc:
        print(f"\nFALLO en el montaje\n{exc}")
        return 2

    chapters = assemble.write_chapters(clips, scene_list, workdir / "chapters.txt",
                                       transitions=transitions)
    total = assemble.audio_duration(out)

    print(f"\nDuracion total : {total / 60:.1f} min")
    print(f"Generado en    : {time.time() - started:.0f}s")
    print(f"Video          : {out}")
    print(f"Capitulos      : {chapters}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="facelessyt.video")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="valida el guion sin renderizar")
    p_check.add_argument("--script", required=True)
    p_check.set_defaults(func=cmd_check)

    p_render = sub.add_parser("render", help="genera el mp4")
    p_render.add_argument("--script", required=True)
    p_render.add_argument("--out")
    p_render.add_argument("--workdir")
    p_render.add_argument("--only", help="lista de ids de escena separados por coma")
    p_render.add_argument("--engine", default="auto", choices=["auto", "piper", "elevenlabs"])
    p_render.add_argument("--music", help="fichero de audio para el fondo (o MUSIC_PATH)")
    p_render.add_argument("--no-motion", action="store_true", help="planos fijos, como antes")
    p_render.add_argument("--no-reveal", action="store_true",
                          help="el terminal aparece entero, sin revelado por lineas")
    p_render.add_argument("--allow-voice-change", action="store_true",
                          help="permite re-locutar el episodio con otro motor")
    p_render.add_argument("--no-transitions", action="store_true", help="corte seco entre escenas")
    p_render.add_argument("--force", action="store_true",
                          help="renderiza aunque el lint de gancho/ritmo falle")
    p_render.set_defaults(func=cmd_render)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
