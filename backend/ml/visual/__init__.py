"""
AceIt Deep Learning visual-analysis package.

Pipeline (see pipeline.py):

    VIDEO
      -> frame_processor      (decode + intelligent frame sampling)
      -> face_analysis        (MediaPipe Face Mesh landmarks + iris)
          |-- emotion_analysis (CNN facial-expression recognition)
          |-- eye_contact      (gaze direction / looking-at-camera)
          |-- gaze / head pose (yaw / pitch / tilt from landmarks)
          '-- posture          (MediaPipe Pose upper-body landmarks)
      -> aggregation          (temporal aggregation of per-frame results)
      -> scoring              (metric -> /10 with configurable weights)

Every analyser is defensive: a failure on a single frame or a single
sub-module is isolated and never crashes the whole request.
"""
