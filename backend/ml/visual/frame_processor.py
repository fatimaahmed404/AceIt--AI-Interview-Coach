"""
Video decoding and intelligent frame sampling.

We decode with OpenCV (falling back to imageio when OpenCV cannot open the
container, e.g. some webm recordings from the browser). Instead of analysing
every frame we sample at ANALYSIS_FPS, capped at MAX_FRAMES, which keeps
processing bounded and responsive.

Yields (timestamp_seconds, frame_bgr) tuples.
"""
import logging

from config import ANALYSIS_FPS, MAX_FRAMES

log = logging.getLogger("aceit.frames")


def probe_video(path):
    """Return (fps, frame_count, duration_seconds). Best-effort."""
    try:
        import cv2

        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        cap.release()
        fps = float(fps) if fps and fps > 0 else 25.0
        count = int(count) if count and count > 0 else 0
        duration = (count / fps) if count else 0.0
        return fps, count, duration
    except Exception as exc:  # noqa: BLE001
        log.warning("probe_video failed: %s", exc)
        return 25.0, 0, 0.0


def iter_sampled_frames(path):
    """
    Yield (timestamp, frame_bgr) sampled at ~ANALYSIS_FPS.

    Tries OpenCV first; if it cannot open or yields no frames, falls back to
    imageio. Raises ValueError if neither backend can read any frame.
    """
    produced = 0
    for ts, frame in _iter_opencv(path):
        produced += 1
        yield ts, frame
        if produced >= MAX_FRAMES:
            return
    if produced == 0:
        for ts, frame in _iter_imageio(path):
            produced += 1
            yield ts, frame
            if produced >= MAX_FRAMES:
                return
    if produced == 0:
        raise ValueError("Could not decode any frames from the video.")


def _iter_opencv(path):
    try:
        import cv2
    except Exception:  # noqa: BLE001
        return
    cap = None
    try:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return
        src_fps = cap.get(cv2.CAP_PROP_FPS) or 0
        src_fps = float(src_fps) if src_fps and src_fps > 0 else 25.0
        step = max(1, int(round(src_fps / max(0.1, ANALYSIS_FPS))))
        idx = 0
        while True:
            ok = cap.grab()
            if not ok:
                break
            if idx % step == 0:
                ok, frame = cap.retrieve()
                if ok and frame is not None:
                    yield idx / src_fps, frame
            idx += 1
    except Exception as exc:  # noqa: BLE001
        log.warning("OpenCV decode error: %s", exc)
    finally:
        if cap is not None:
            cap.release()


def _iter_imageio(path):
    try:
        import imageio.v3 as iio
        import numpy as np
        import cv2
    except Exception as exc:  # noqa: BLE001
        log.warning("imageio fallback unavailable: %s", exc)
        return
    try:
        meta = iio.immeta(path, plugin="pyav")
        src_fps = float(meta.get("fps", 25.0)) or 25.0
    except Exception:  # noqa: BLE001
        src_fps = 25.0
    step = max(1, int(round(src_fps / max(0.1, ANALYSIS_FPS))))
    try:
        for idx, frame_rgb in enumerate(iio.imiter(path, plugin="pyav")):
            if idx % step != 0:
                continue
            frame_bgr = cv2.cvtColor(np.asarray(frame_rgb), cv2.COLOR_RGB2BGR)
            yield idx / src_fps, frame_bgr
    except Exception as exc:  # noqa: BLE001
        log.warning("imageio decode error: %s", exc)
