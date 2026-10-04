"""
Temporal aggregation of per-frame visual results.

Takes the list of per-frame records produced by the pipeline and condenses
them into summary metrics plus a timeline of notable events. Everything here
is pure Python / numpy and has no heavy dependencies, so it is easy to unit
test in isolation.
"""
from collections import Counter

from .eye_contact import STATE_CAMERA
from .posture import STATE_GOOD, STATE_SLIGHT, STATE_SLOUCHED, STATE_NO_BODY
from .emotion_analysis import INTERVIEW_CATEGORIES


def _pct(part, whole):
    return round((part / whole) * 100, 1) if whole else 0.0


def aggregate(frames):
    """
    frames: list of dicts, each like:
        {"timestamp": float, "face_detected": bool, "multiple_faces": bool,
         "emotion": {...}|None, "eye": {...}|None, "head": {...}|None,
         "posture": {...}|None}

    Returns a dict with facial_expression / eye_contact / posture /
    head_movement summaries and a merged timeline.
    """
    total = len(frames)
    face_frames = [f for f in frames if f.get("face_detected")]
    valid_face = len(face_frames)
    multi_face_frames = sum(1 for f in frames if f.get("multiple_faces"))

    return {
        "frames_analyzed": total,
        "face_detected_frames": valid_face,
        "multiple_faces_detected": multi_face_frames > 0,
        "facial_expression": _agg_emotion(face_frames),
        "eye_contact": _agg_eye_contact(face_frames),
        "head_movement": _agg_head(face_frames),
        "posture": _agg_posture(frames),
        "timeline": _build_timeline(frames),
    }


def _agg_emotion(face_frames):
    emotions = [f["emotion"] for f in face_frames if f.get("emotion")]
    if not emotions:
        return {"available": False, "dominant": None, "distribution": {}, "confidence": 0.0}

    labels = [e["emotion"] for e in emotions]
    counts = Counter(labels)
    n = len(labels)
    distribution = {c: _pct(counts.get(c, 0), n) for c in INTERVIEW_CATEGORIES}
    dominant = counts.most_common(1)[0][0]
    avg_conf = round(sum(e["confidence"] for e in emotions) / n, 3)

    nervous_freq = _pct(counts.get("nervous", 0), n)
    engaged_freq = _pct(counts.get("confident", 0), n)
    # Emotional stability = fraction of frames matching the dominant emotion.
    stability = _pct(counts.get(dominant, 0), n)

    return {
        "available": True,
        "dominant": dominant,
        "confidence": avg_conf,
        "distribution": distribution,
        "emotional_stability": stability,
        "nervous_expression_frequency": nervous_freq,
        "engaged_expression_frequency": engaged_freq,
    }


def _agg_eye_contact(face_frames):
    eyes = [f["eye"] for f in face_frames if f.get("eye")]
    valid = len(eyes)
    if not valid:
        return {"available": False, "percentage": 0.0, "valid_frames": 0}
    looking = sum(1 for e in eyes if e["state"] == STATE_CAMERA)
    pct = _pct(looking, valid)
    state_counts = Counter(e["state"] for e in eyes)
    return {
        "available": True,
        "percentage": pct,
        "valid_frames": valid,
        "state_distribution": {k: _pct(v, valid) for k, v in state_counts.items()},
    }


def _agg_head(face_frames):
    heads = [f["head"] for f in face_frames if f.get("head")]
    valid = len(heads)
    if not valid:
        return {"available": False, "stability": 0.0}
    import numpy as np

    yaws = np.array([h["yaw"] for h in heads])
    pitches = np.array([h["pitch"] for h in heads])
    rolls = np.array([h["roll"] for h in heads])
    # Stability: lower angular variance -> higher stability (0..10 internal).
    spread = float(np.std(yaws) + np.std(pitches) + np.std(rolls))
    stability = max(0.0, 1.0 - min(1.0, spread / 60.0))  # 0..1
    events = Counter(h["event"] for h in heads if h.get("event"))
    looking_down = _pct(events.get("looking_down", 0), valid)
    return {
        "available": True,
        "stability": round(stability, 3),
        "valid_frames": valid,
        "looking_down_frequency": looking_down,
        "event_counts": dict(events),
        "mean_yaw": round(float(yaws.mean()), 2),
        "mean_pitch": round(float(pitches.mean()), 2),
    }


def _agg_posture(frames):
    postures = [f["posture"] for f in frames if f.get("posture")]
    detected = [p for p in postures if p["state"] != STATE_NO_BODY]
    valid = len(detected)
    if not valid:
        return {"available": False, "good_posture_percentage": 0.0, "valid_frames": 0}
    counts = Counter(p["state"] for p in detected)
    good = _pct(counts.get(STATE_GOOD, 0), valid)
    slouched = _pct(counts.get(STATE_SLOUCHED, 0) + counts.get(STATE_SLIGHT, 0), valid)
    # Stability from shoulder-symmetry variance.
    import numpy as np

    syms = np.array([p.get("shoulder_symmetry", 0) for p in detected])
    stability = max(0.0, 1.0 - min(1.0, float(np.std(syms)) * 4))
    return {
        "available": True,
        "good_posture_percentage": good,
        "slouched_percentage": slouched,
        "stability": round(stability, 3),
        "valid_frames": valid,
        "state_distribution": {k: _pct(v, valid) for k, v in counts.items()},
    }


def _build_timeline(frames):
    """
    Produce a compact event timeline. We collapse consecutive identical events
    into single entries with a duration so the UI shows meaningful moments
    rather than one entry per frame.
    """
    raw = []
    for f in frames:
        ts = round(f.get("timestamp", 0.0), 1)
        if not f.get("face_detected"):
            raw.append((ts, "face_not_detected"))
            continue
        eye = f.get("eye")
        if eye and eye["state"] != STATE_CAMERA:
            raw.append((ts, eye["state"]))
        elif eye and eye["state"] == STATE_CAMERA:
            raw.append((ts, "good_eye_contact"))
        head = f.get("head")
        if head and head.get("event"):
            raw.append((ts, head["event"]))
        posture = f.get("posture")
        if posture and posture["state"] in (STATE_SLOUCHED, STATE_SLIGHT):
            raw.append((ts, "slouch_detected"))

    # Collapse consecutive same-event entries.
    timeline = []
    for ts, event in raw:
        if timeline and timeline[-1]["event"] == event and ts - timeline[-1]["_last"] <= 1.5:
            timeline[-1]["duration"] = round(ts - timeline[-1]["timestamp"], 1)
            timeline[-1]["_last"] = ts
        else:
            timeline.append({"timestamp": ts, "event": event, "duration": 0.0, "_last": ts})
    for t in timeline:
        t.pop("_last", None)
    # Keep only the most informative events (drop very short good-eye-contact spam).
    return timeline
