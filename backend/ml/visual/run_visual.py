"""
Standalone CLI entry point for the visual pipeline.

The visual Deep Learning stack (MediaPipe 0.10.x + protobuf 4 + LiteRT) is not
dependency-compatible with the main backend environment (TensorFlow 2.20 +
protobuf 5), so the Flask app runs this script in a dedicated virtual
environment (.venv-visual) as a subprocess.

Usage:
    python -m ml.visual.run_visual <video_path>

Progress stages are written to STDERR (one per line, prefixed "PROGRESS:").
The final JSON result is written to STDOUT.
"""
import sys
import json
import os

# Ensure the backend root is importable when run with `python path/to/run_visual.py`.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from ml.visual.pipeline import analyze_video  # noqa: E402


def main(argv):
    if len(argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: run_visual.py <video_path>"}))
        return 1
    video_path = argv[1]
    if not os.path.exists(video_path):
        print(json.dumps({"ok": False, "error": f"Video not found: {video_path}"}))
        return 1

    def progress(stage):
        sys.stderr.write(f"PROGRESS:{stage}\n")
        sys.stderr.flush()

    result = analyze_video(video_path, progress=progress)
    sys.stdout.write(json.dumps(result))
    sys.stdout.flush()
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
