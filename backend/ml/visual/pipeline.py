"""
Top-level visual-analysis pipeline orchestrator.

    analyze_video(path) -> {
        "ok": bool,
        "error": str|None,
        "meta": {fps, duration, frames_analyzed},
        "metrics": <aggregated metrics>,
        "scores": {visual: float, components: {...}},
        "timeline": [...],
        "feedback": [...],
    }

The orchestrator is defensive at three levels:
  1. video-open / decode failures -> returns ok=False with a friendly error
  2. per-frame failures           -> isolated inside each analyser (return None)
  3. per-module unavailability    -> that metric is simply marked unavailable
"""
import logging

from .frame_processor import probe_video, iter_sampled_frames
from .face_analysis import FaceMesh
from .posture import PostureAnalyzer
from .emotion_analysis import analyze_face_emotion
from .eye_contact import estimate_eye_contact
from .gaze import estimate_head_pose
from .aggregation import aggregate
from .scoring import score_visual
from .feedback import generate_feedback

log = logging.getLogger("aceit.pipeline")


def analyze_video(path, progress=None):
    """
    Analyse a recorded interview video.

    `progress` is an optional callable(stage:str) used to report progress.
    """
    def report(stage):
        if progress:
            try:
                progress(stage)
            except Exception:  # noqa: BLE001
                pass

    report("Loading video...")
    fps, frame_count, duration = probe_video(path)

    face_mesh = FaceMesh()
    posture_analyzer = PostureAnalyzer()

    frames = []
    report("Processing frames...")
    try:
        for ts, frame in iter_sampled_frames(path):
            record = {"timestamp": ts, "face_detected": False, "multiple_faces": False,
                      "emotion": None, "eye": None, "head": None, "posture": None}

            # --- Face mesh (shared) ---
            face = face_mesh.process(frame)
            record["face_detected"] = face["face_detected"]
            record["multiple_faces"] = face["multiple_faces"]
            landmarks = face["landmarks"]
            frame_size = face["frame_size"]

            if face["face_detected"]:
                # Emotion CNN
                if face["face_crop"] is not None:
                    record["emotion"] = analyze_face_emotion(face["face_crop"])
                # Eye contact / gaze
                record["eye"] = estimate_eye_contact(landmarks)
                # Head pose
                record["head"] = estimate_head_pose(landmarks, frame_size)

            # --- Posture (independent of face) ---
            record["posture"] = posture_analyzer.process(frame)
            frames.append(record)
    except ValueError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "meta": {"fps": fps, "duration": duration, "frames_analyzed": 0},
            "metrics": {}, "scores": {}, "timeline": [], "feedback": [],
        }
    except Exception as exc:  # noqa: BLE001 - never leak a raw stack trace
        log.exception("Unexpected pipeline failure")
        return {
            "ok": False,
            "error": f"Video analysis failed: {exc}",
            "meta": {"fps": fps, "duration": duration, "frames_analyzed": len(frames)},
            "metrics": {}, "scores": {}, "timeline": [], "feedback": [],
        }
    finally:
        face_mesh.close()
        posture_analyzer.close()

    if not frames:
        return {
            "ok": False,
            "error": "No frames could be analysed from the recording.",
            "meta": {"fps": fps, "duration": duration, "frames_analyzed": 0},
            "metrics": {}, "scores": {}, "timeline": [], "feedback": [],
        }

    report("Aggregating results...")
    aggregated = aggregate(frames)

    report("Scoring...")
    scores = score_visual(aggregated)

    report("Generating feedback...")
    feedback = generate_feedback(aggregated, scores)

    report("Complete.")
    return {
        "ok": True,
        "error": None,
        "meta": {
            "fps": round(fps, 2),
            "duration": round(duration, 2),
            "frames_analyzed": aggregated["frames_analyzed"],
            "face_detected_frames": aggregated["face_detected_frames"],
        },
        "metrics": aggregated,
        "scores": scores,
        "timeline": aggregated.get("timeline", []),
        "feedback": feedback,
    }
