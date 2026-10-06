"""
Extract an audio WAV track from a recorded video (e.g. browser webm/mp4).

The browser records a single webm blob containing both video and audio. The
audio model (librosa + TensorFlow) needs a decodable WAV, and librosa cannot
read webm directly in this environment (no ffmpeg audioread backend). We use
the ffmpeg binary bundled with imageio-ffmpeg to transcode the audio track to
a mono 22.05 kHz WAV, which librosa/soundfile read reliably.
"""
import os
import uuid
import logging
import subprocess

log = logging.getLogger("aceit.audio_extract")


def _ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # noqa: BLE001
        log.warning("Bundled ffmpeg unavailable: %s", exc)
        return None


def has_ffmpeg():
    return _ffmpeg_exe() is not None


def extract_wav(video_path, out_dir):
    """
    Transcode the audio track of `video_path` to a mono 22.05 kHz WAV in
    `out_dir`. Returns the WAV path, or None if extraction fails (e.g. the
    recording has no audio track).
    """
    ff = _ffmpeg_exe()
    if ff is None or not video_path or not os.path.exists(video_path):
        return None
    os.makedirs(out_dir, exist_ok=True)
    wav_path = os.path.join(out_dir, f"{uuid.uuid4().hex}.wav")
    cmd = [
        ff, "-y", "-i", video_path,
        "-vn",                 # drop video
        "-acodec", "pcm_s16le",
        "-ar", "22050",
        "-ac", "1",
        wav_path,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=120)
    except Exception as exc:  # noqa: BLE001
        log.warning("ffmpeg audio extraction failed: %s", exc)
        return None
    if proc.returncode != 0 or not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
        log.info("No usable audio track extracted from %s", os.path.basename(video_path))
        if os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except OSError:
                pass
        return None
    return wav_path
