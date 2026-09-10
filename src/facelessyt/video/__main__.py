"""Genera el video a partir del guion.

  python -m facelessyt.video render --script scripts/01-outlier-agent.yaml
  python -m facelessyt.video render --script ... --only hook-1,hook-2   (prueba rapida)
  python -m facelessyt.video check  --script ...                        (sin render)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml

from . import assemble, scenes


def load_script(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def cmd_check(args: argparse.Namespace) -> int:
    """Valida el guion sin generar nada: que toda escena se sepa dibujar."""
    spec = load_script(Path(args.script))
    scene_list = spec["scenes"]

    problems, words = [], 0
    for scene in scene_list:
        words += len(scene.get("narration", "").split())
        key = scene.get("visual", {}).get("content", "")
        if key not in scenes.CONTENT and scene.get("visual", {}).get("type") != "text":
            problems.append(f"  {scene['id']}: no hay visual para '{key}'")
        if not scene.get("narration", "").strip():
            problems.append(f"  {scene['id']}: sin narracion")

    # ~150 palabras por minuto es el ritmo de locucion tecnica comoda.
    estimate = words / 150
    print(f"Escenas      : {len(scene_list)}")
    print(f"Palabras     : {words}")
    print(f"Duracion est.: {estimate:.1f} min (objetivo {spec['video'].get('target_minutes')})")

    if problems:
        print(f"\n{len(problems)} problema(s):")
        print("\n".join(problems))
        return 1
    print("\nOK: todas las escenas se pueden renderizar")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    spec = load_script(Path(args.script))
    video_id = spec["video"]["id"]
    scene_list = spec["scenes"]

    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        scene_list = [s for s in scene_list if s["id"] in wanted]
        if not scene_list:
            print(f"Ninguna escena coincide con: {args.only}")
            return 1

    workdir = Path(args.workdir or f"data/video/{video_id}")
    workdir.mkdir(parents=True, exist_ok=True)

    clips, started = [], time.time()
    for i, scene in enumerate(scene_list, 1):
        print(f"[{i:2}/{len(scene_list)}] {scene['id']:24}", end=" ", flush=True)
        try:
            clip = assemble.build_scene(scene, workdir, engine=args.engine)
        except (scenes.SceneError, assemble.AssembleError) as exc:
            print("FALLO")
            print(f"\n{exc}")
            return 2
        clips.append(clip)
        print(f"{clip.duration:5.1f}s  ({clip.words} palabras)")

    total = sum(c.duration for c in clips)
    out = Path(args.out or f"data/video/{video_id}.mp4")
    assemble.concat(clips, out, workdir)

    chapters = assemble.write_chapters(clips, scene_list, workdir / "chapters.txt")

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
    p_render.set_defaults(func=cmd_render)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
