"""
Centralised, transparent scoring.

Every metric is scored out of 10. Visual sub-scores combine into a single
"visual" score using VISUAL_WEIGHTS, and the three modalities combine into an
overall score using OVERALL_WEIGHTS (both from config.py). Weights are never
hard-coded elsewhere.

Scoring logic is intentionally simple and documented:
  - eye_contact score   = percentage / 10            (78% -> 7.8)
  - posture score       = good_posture_percentage/10 (81% -> 8.1)
  - expression score    = engagement-weighted blend of the emotion distribution
  - head_movement score = stability (0..1) * 10, penalised by looking-down freq

Missing modalities are dropped and the remaining weights are renormalised, so
a session with no video still produces a valid overall score.
"""
from config import VISUAL_WEIGHTS, OVERALL_WEIGHTS


def _clamp(x, lo=0.0, hi=10.0):
    return round(max(lo, min(hi, x)), 2)


def score_eye_contact(agg):
    if not agg.get("available"):
        return None
    return _clamp(agg["percentage"] / 10.0)


def score_posture(agg):
    if not agg.get("available"):
        return None
    base = agg["good_posture_percentage"] / 10.0
    # Nudge by stability so a jittery-but-upright candidate is not perfect.
    stability_bonus = (agg.get("stability", 0.0) - 0.5) * 2.0  # -1..+1
    return _clamp(base + stability_bonus)


def score_expression(agg):
    if not agg.get("available"):
        return None
    dist = agg.get("distribution", {})
    # Engagement blend: confident is best, neutral is fine, confused/nervous cost.
    engaged = dist.get("confident", 0.0)
    neutral = dist.get("neutral", 0.0)
    confused = dist.get("confused", 0.0)
    nervous = dist.get("nervous", 0.0)
    raw = (engaged * 1.0 + neutral * 0.75 + confused * 0.4 + nervous * 0.3)  # 0..100
    return _clamp(raw / 10.0)


def score_head_movement(agg):
    if not agg.get("available"):
        return None
    base = agg.get("stability", 0.0) * 10.0
    penalty = (agg.get("looking_down_frequency", 0.0) / 100.0) * 3.0
    return _clamp(base - penalty)


def score_visual(aggregated):
    """
    Combine the four visual sub-scores into one visual score + per-metric scores.
    Returns {"score": float|None, "components": {metric: score}}.
    """
    components = {
        "eye_contact": score_eye_contact(aggregated.get("eye_contact", {})),
        "posture": score_posture(aggregated.get("posture", {})),
        "facial_expression": score_expression(aggregated.get("facial_expression", {})),
        "head_movement": score_head_movement(aggregated.get("head_movement", {})),
    }
    combined = _weighted_mean(components, VISUAL_WEIGHTS)
    return {"score": combined, "components": components}


def score_overall(voice=None, text=None, visual=None):
    """
    Combine modality scores (each /10, may be None) into an overall score.
    Renormalises over whichever modalities are present.
    """
    modality_scores = {"voice": voice, "text": text, "visual": visual}
    return _weighted_mean(modality_scores, OVERALL_WEIGHTS)


def _weighted_mean(values, weights):
    """Weighted mean over keys whose value is not None; renormalises weights."""
    num = 0.0
    denom = 0.0
    for key, val in values.items():
        if val is None:
            continue
        w = weights.get(key, 0.0)
        num += w * val
        denom += w
    if denom == 0:
        return None
    return _clamp(num / denom)
