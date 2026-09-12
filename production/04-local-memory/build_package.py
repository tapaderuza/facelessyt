"""Validate the episode spec and build local preproduction artifacts, not a film.

Run from the repository: python production/04-local-memory/build_package.py
No network, publishing, model download or TTS. Generated files stay in this folder.
"""
import hashlib
import json
from pathlib import Path
import re

import yaml

from facelessyt.memory_budget import demo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def validate(spec, evidence):
    errors = []
    if evidence != demo():
        errors.append("Evidence differs from current executable calculator")
    end, seen, words = 0, set(), 0
    for scene in spec["scenes"]:
        if scene["id"] in seen or scene["start"] != end or scene["end"] <= scene["start"]:
            errors.append(f"Timeline/id conflict: {scene['id']}")
        seen.add(scene["id"])
        end = scene["end"]
        if not scene["evidence"] or any(key not in evidence for key in scene["evidence"]):
            errors.append(f"Missing evidence: {scene['id']}")
        beats = [b[0] for b in scene["beats"]] + [scene["end"] - scene["start"]]
        if beats[0] != 0 or any(b <= a or b - a > 6 for a, b in zip(beats, beats[1:])):
            errors.append(f"Beat gap >6s or invalid order: {scene['id']}")
        count = len(re.findall(r"\b[\w'-]+\b", scene["narration"]))
        words += count
        wpm = count * 60 / (scene["end"] - scene["start"])
        if not 80 <= wpm <= 180:
            errors.append(f"Narration timing implausible: {scene['id']} {wpm:.0f} wpm")
    if end != spec["duration_target_seconds"]:
        errors.append("Duration mismatch")
    if end * spec["render"]["fps"] != spec["render"]["frame_count_target"]:
        errors.append("Frame count mismatch")
    if re.match(r"(?i)\s*(hello|hi everyone|welcome|hey guys)", spec["scenes"][0]["narration"]):
        errors.append("Generic greeting at second zero")
    if not spec["render"].get("persistent_demo_label"):
        errors.append("Missing illustration disclosure")
    return {"checks_passed": not errors, "errors": errors, "narration_words": words,
            "target_seconds": end, "estimated_wpm": round(words * 60 / end, 1),
            "scope": "Structural preproduction checks only, not finished-video QA",
            "render_complete": False, "audio_timing_locked": False,
            "publication_ready": False}


def main():
    spec = yaml.safe_load((HERE / "episode.yaml").read_text(encoding="utf-8"))
    evidence = json.loads((HERE / spec["evidence_file"]).read_text(encoding="utf-8"))
    result = validate(spec, evidence)
    if result["errors"]:
        raise ValueError("\n".join(result["errors"]))
    text = [f"# Episodio 04 — {spec['title']}", "", "Guion de locución en inglés. Timestamps objetivo; ajustar al audio real.",
            "Ejemplo matemático ejecutado; no se ha ejecutado ni medido un LLM.", ""]
    for scene in spec["scenes"]:
        seconds = scene["start"]
        text += [f"## {seconds // 60:02d}:{seconds % 60:02d} — {scene['chapter']} ({scene['id']})", "", scene["narration"], ""]
    (HERE / "GUION.md").write_text("\n".join(text), encoding="utf-8")
    (HERE / "render-spec.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    template = (HERE / "preview-template.html").read_text(encoding="utf-8")
    payload = json.dumps(evidence).replace("<", "\\u003c")
    (HERE / "animatic.html").write_text(template.replace("__EVIDENCE_JSON__", payload), encoding="utf-8")
    result["sha256"] = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                         for name in ("episode.yaml", "memory-evidence.json", "render-spec.json")}
    (HERE / "preproduction-qa.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
