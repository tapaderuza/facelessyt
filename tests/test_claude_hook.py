"""El hook de Claude Code (tools/claude_hook_check.py): tres casos, un contrato."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "tools" / "claude_hook_check.py"


def run_hook(file_path: str) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": file_path}})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True,
                          text=True, cwd=ROOT, timeout=120)


class ClaudeHookTests(unittest.TestCase):
    def test_otro_fichero_exit_0_sin_salida(self):
        r = run_hook(str(ROOT / "README.md"))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stderr, "")

    def test_guion_malo_exit_2_con_errores(self):
        bad = ROOT / "scripts" / "_hook_test_bad.yaml"
        bad.parent.mkdir(exist_ok=True)
        bad.write_text(
            "video: {id: t}\nscenes:\n"
            "  - id: hook-1\n    narration: This channel has zero subscribers and no videos yet.\n"
            "    visual: {type: text, content: x}\n", encoding="utf-8")
        try:
            r = run_hook(str(bad))
        finally:
            bad.unlink()
        self.assertEqual(r.returncode, 2)
        self.assertIn("hook-self-talk", r.stderr)

    def test_guion_bueno_exit_0(self):
        good = ROOT / "scripts" / "_hook_test_good.yaml"
        good.parent.mkdir(exist_ok=True)
        good.write_text(
            "video: {id: t}\nscenes:\n"
            "  - id: hook-1\n    narration: Watch this, 24 calls paid twice.\n    visual: {type: text, content: a}\n"
            "  - id: hook-2\n    narration: Here is the bill.\n    visual: {type: text, content: b}\n"
            "  - id: hook-3\n    narration: And here is the fix.\n    visual: {type: text, content: c}\n",
            encoding="utf-8")
        try:
            r = run_hook(str(good))
        finally:
            good.unlink()
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
