"""
Bridge between the Flask app (main venv, TensorFlow) and the visual Deep
Learning pipeline (isolated .venv-visual with MediaPipe + LiteRT).

Because the two dependency sets cannot coexist in one interpreter, the visual
pipeline runs as a subprocess using the dedicated venv's python. This module
locates that interpreter, invokes `ml.visual.run_visual`, captures progress on
stderr and the JSON result on stdout, and returns a normalised dict.
"""
import os
import sys
import json
import subprocess
import logging

log = logging.getLogger("aceit.visual_runner")

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_BACKEND_DIR, ".."))


def _find_visual_python():
    """Locate the python interpreter of the isolated visual venv."""
    candidates = [
        os.environ.get("ACEIT_VISUAL_PYTHON"),
        os.path.join(_PROJECT_ROOT, ".venv-visual", "bin", "python"),
        os.path.join(_PROJECT_ROOT, ".venv-visual", "Scripts", "python.exe"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def visual_pipeline_available():
    return _find_visual_python() is not None


def run_visual_analysis(video_path, timeout=600, on_progress=None):
    """
    Run the visual pipeline on `video_path`.

    Returns the pipeline result dict. On any failure returns a dict with
    ok=False and a human-friendly error (never a raw stack trace).
    """
    py = _find_visual_python()
    if py is None:
        return {
            "ok": False,
            "error": "Visual analysis environment is not installed (.venv-visual missing).",
            "meta": {}, "metrics": {}, "scores": {}, "timeline": [], "feedback": [],
        }
    if not os.path.exists(video_path):
        return {"ok": False, "error": "Uploaded video could not be found on the server.",
                "meta": {}, "metrics": {}, "scores": {}, "timeline": [], "feedback": []}

    cmd = [py, "-m", "ml.visual.run_visual", video_path]
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=_BACKEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Stream stderr for progress while the process runs.
        stderr_lines = []
        if on_progress is not None and proc.stderr is not None:
            for line in proc.stderr:
                stderr_lines.append(line)
                if line.startswith("PROGRESS:"):
                    try:
                        on_progress(line[len("PROGRESS:"):].strip())
                    except Exception:  # noqa: BLE001
                        pass
            stdout, _ = proc.communicate(timeout=timeout)
        else:
            stdout, stderr = proc.communicate(timeout=timeout)
            stderr_lines = (stderr or "").splitlines(keepends=True)
    except subprocess.TimeoutExpired:
        proc.kill()
        return {"ok": False, "error": "Video analysis timed out.",
                "meta": {}, "metrics": {}, "scores": {}, "timeline": [], "feedback": []}
    except Exception as exc:  # noqa: BLE001
        log.exception("Failed to launch visual subprocess")
        return {"ok": False, "error": f"Could not start visual analysis: {exc}",
                "meta": {}, "metrics": {}, "scores": {}, "timeline": [], "feedback": []}

    if not stdout or not stdout.strip():
        err_tail = "".join(stderr_lines)[-400:]
        log.error("Visual subprocess produced no output. stderr tail: %s", err_tail)
        return {"ok": False, "error": "Visual analysis produced no result.",
                "meta": {}, "metrics": {}, "scores": {}, "timeline": [], "feedback": []}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        log.error("Visual subprocess returned invalid JSON: %s", stdout[:400])
        return {"ok": False, "error": "Visual analysis returned an unreadable result.",
                "meta": {}, "metrics": {}, "scores": {}, "timeline": [], "feedback": []}
