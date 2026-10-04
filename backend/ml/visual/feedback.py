"""
Actionable, descriptive feedback generation.

Feedback is derived from aggregated metrics and is deliberately *descriptive*
rather than psychological. We never say "you are nervous"; we describe what the
analysis observed (e.g. "several frames showed expressions mapped to the
configured nervous-expression category").
"""


def generate_feedback(aggregated, visual_scores):
    """Return a list of feedback dicts: {category, message, score}."""
    tips = []

    # --- Eye contact ---
    eye = aggregated.get("eye_contact", {})
    if eye.get("available"):
        pct = eye["percentage"]
        score = visual_scores["components"].get("eye_contact")
        if pct >= 75:
            msg = (f"You maintained eye contact with the camera for about {pct}% of the "
                   "response, which reads as engaged and attentive.")
        elif pct >= 50:
            msg = (f"Your eye contact was maintained for {pct}% of the response. Try looking "
                   "directly at the camera more consistently.")
        else:
            msg = (f"Eye contact with the camera was detected for only {pct}% of the response. "
                   "Position the camera at eye level and look into it when speaking.")
        tips.append({"category": "Eye contact", "message": msg, "score": score})

    # --- Posture ---
    posture = aggregated.get("posture", {})
    if posture.get("available"):
        good = posture["good_posture_percentage"]
        score = visual_scores["components"].get("posture")
        if good >= 75:
            msg = f"You held a stable, upright posture for about {good}% of the answer."
        elif good >= 50:
            msg = (f"You kept good posture for {good}% of the answer, but your shoulders became "
                   "slightly slouched during parts of the response.")
        else:
            msg = (f"Upright posture was detected for {good}% of the answer. Sitting back with "
                   "level shoulders will project more confidence.")
        tips.append({"category": "Posture", "message": msg, "score": score})

    # --- Facial expression ---
    expr = aggregated.get("facial_expression", {})
    if expr.get("available"):
        dominant = expr["dominant"]
        nervous = expr.get("nervous_expression_frequency", 0)
        score = visual_scores["components"].get("facial_expression")
        if dominant == "neutral":
            msg = ("Your facial expression stayed mostly neutral. Consider showing a slightly "
                   "more engaged expression when discussing your strengths.")
        elif dominant == "confident":
            msg = "Your expression read as engaged and positive for most of the response."
        else:
            msg = (f"The dominant expression category was '{dominant}'. "
                   f"About {nervous}% of frames showed expressions mapped to the configured "
                   "nervous-expression category.")
        tips.append({"category": "Facial expression", "message": msg, "score": score})

    # --- Head movement ---
    head = aggregated.get("head_movement", {})
    if head.get("available"):
        down = head.get("looking_down_frequency", 0)
        score = visual_scores["components"].get("head_movement")
        if down >= 25:
            msg = (f"Frequent downward head movement was detected during roughly {down}% of the "
                   "response. Keeping your head up helps maintain presence.")
        else:
            msg = "Your head position stayed relatively stable throughout the answer."
        tips.append({"category": "Head movement", "message": msg, "score": score})

    # --- Data quality notes ---
    if aggregated.get("multiple_faces_detected"):
        tips.append({
            "category": "Recording",
            "message": "More than one face was detected in some frames; make sure only you are "
                       "visible for the most accurate analysis.",
            "score": None,
        })
    if aggregated.get("frames_analyzed") and not aggregated.get("face_detected_frames"):
        tips.append({
            "category": "Recording",
            "message": "No face was reliably detected in the video, so visual metrics could not "
                       "be computed. Check your lighting and camera framing.",
            "score": None,
        })

    return tips
