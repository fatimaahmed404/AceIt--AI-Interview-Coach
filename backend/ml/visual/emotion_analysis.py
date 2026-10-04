"""
Facial Expression / Emotion analysis.

Deep Learning component (Intro to Deep Learning course requirement).

A pretrained Convolutional Neural Network (CNN) classifies a cropped face
image into one of the seven FER2013 emotion classes. The model is the one
bundled with the `fer` package (data/emotion_model_quantized.tflite): a small
VGG-style CNN trained on the FER2013 dataset. We run it through LiteRT
(ai-edge-litert) so the visual environment does not need full TensorFlow,
which keeps it dependency-compatible with MediaPipe 0.10.x.

NOTE: this is a *pretrained* model. We did not train it from scratch; we
integrate it and add a mapping + temporal-aggregation layer on top.

CNN inference per face:
    64x64 grayscale face crop -> CNN -> softmax over 7 classes

Because the interview-coaching domain cares about "confident / nervous /
confused / neutral" rather than raw FER classes, we apply a documented
mapping layer (RAW_TO_INTERVIEW) instead of pretending the model predicts
those labels directly.
"""
import os
import logging

import numpy as np

log = logging.getLogger("aceit.emotion")

# Raw FER2013 class order produced by the bundled CNN (output shape (None, 7)).
FER_CLASSES = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

# ---------------------------------------------------------------------------
# Mapping layer: raw FER2013 emotion -> interview-performance category.
# This is a heuristic, interview-domain mapping and is documented so the
# behaviour is transparent (we never claim the CNN directly predicts these).
#   confident -> relaxed / positive engagement
#   nervous   -> tension-associated expressions
#   confused  -> uncertainty-associated expressions
#   neutral   -> composed / neutral
# ---------------------------------------------------------------------------
RAW_TO_INTERVIEW = {
    "happy": "confident",
    "surprise": "confused",
    "neutral": "neutral",
    "sad": "nervous",
    "fear": "nervous",
    "angry": "nervous",
    "disgust": "confused",
}

INTERVIEW_CATEGORIES = ["confident", "nervous", "confused", "neutral"]


class EmotionAnalyzer:
    """Lazy-loading wrapper around the pretrained FER2013 CNN."""

    def __init__(self):
        self._model = None
        self._in = None
        self._out = None
        self._input_size = (64, 64)
        self._load_error = None

    def _ensure_model(self):
        if self._model is not None or self._load_error is not None:
            return
        try:
            import fer
            try:
                from ai_edge_litert.interpreter import Interpreter
            except Exception:  # noqa: BLE001 - fall back to tflite_runtime / tf.lite
                try:
                    from tflite_runtime.interpreter import Interpreter  # type: ignore
                except Exception:
                    import tensorflow as tf  # type: ignore
                    Interpreter = tf.lite.Interpreter

            model_path = os.path.join(
                os.path.dirname(fer.__file__), "data", "emotion_model_quantized.tflite"
            )
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Pretrained emotion CNN not found at {model_path}")
            interp = Interpreter(model_path=model_path)
            interp.allocate_tensors()
            self._model = interp
            self._in = interp.get_input_details()[0]
            self._out = interp.get_output_details()[0]
            shape = self._in["shape"]  # [1, H, W, 1]
            if len(shape) == 4:
                self._input_size = (int(shape[2]), int(shape[1]))  # (w, h)
            log.info("Loaded emotion CNN (tflite), input=%s", shape)
        except Exception as exc:  # noqa: BLE001 - isolate model-load failures
            self._load_error = str(exc)
            log.warning("Emotion CNN unavailable: %s", exc)

    @property
    def available(self):
        self._ensure_model()
        return self._model is not None

    def predict(self, face_bgr):
        """
        Run the CNN on a single BGR face crop (numpy array).

        Returns a dict:
            {"emotion": <interview category>, "raw_emotion": <fer class>,
             "confidence": float, "distribution": {interview_cat: prob}}
        or None if the model is unavailable or the crop is invalid.
        """
        self._ensure_model()
        if self._model is None or face_bgr is None or face_bgr.size == 0:
            return None
        try:
            import cv2

            gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
            w, h = self._input_size
            resized = cv2.resize(gray, (w, h), interpolation=cv2.INTER_AREA)
            arr = resized.astype("float32") / 255.0
            arr = np.expand_dims(arr, axis=(0, -1)).astype(self._in["dtype"])  # (1, h, w, 1)
            self._model.set_tensor(self._in["index"], arr)
            self._model.invoke()
            probs = self._model.get_tensor(self._out["index"])[0]
        except Exception as exc:  # noqa: BLE001 - isolate per-frame failures
            log.debug("Emotion inference failed for a frame: %s", exc)
            return None

        raw_idx = int(np.argmax(probs))
        raw_emotion = FER_CLASSES[raw_idx]
        interview_emotion = RAW_TO_INTERVIEW.get(raw_emotion, "neutral")

        # Collapse the 7-class distribution into the 4 interview categories.
        distribution = {c: 0.0 for c in INTERVIEW_CATEGORIES}
        for i, cls in enumerate(FER_CLASSES):
            distribution[RAW_TO_INTERVIEW.get(cls, "neutral")] += float(probs[i])

        return {
            "emotion": interview_emotion,
            "raw_emotion": raw_emotion,
            "confidence": round(float(probs[raw_idx]), 4),
            "distribution": {k: round(v, 4) for k, v in distribution.items()},
        }


# Module-level singleton so the CNN is loaded only once per process.
_analyzer = EmotionAnalyzer()


def analyze_face_emotion(face_bgr):
    return _analyzer.predict(face_bgr)


def emotion_model_available():
    return _analyzer.available


def model_info():
    """Metadata for the model-information page."""
    return {
        "name": "FER2013 CNN (pretrained)",
        "library": "fer (bundled emotion_model_quantized.tflite) run via LiteRT",
        "type": "Convolutional Neural Network",
        "pretrained": True,
        "trained_from_scratch": False,
        "input": "64x64 grayscale face crop, normalised to [0,1]",
        "output": "softmax over 7 FER2013 classes",
        "raw_classes": FER_CLASSES,
        "interview_mapping": RAW_TO_INTERVIEW,
        "interview_categories": INTERVIEW_CATEGORIES,
    }
