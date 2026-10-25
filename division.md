# AceIt — Project Work Division

**Project:** AceIt — AI-Powered Interview Coach
**Course:** Intro to Deep Learning
**Team Members:** Amina | Zaina | Fatima

---

## Overview of the System

AceIt analyses interview performance across three modalities:

| Modality | What it does |
|----------|-------------|
| **Voice** | Audio clarity/accent detection via a trained TensorFlow neural network |
| **Text** | Confidence, toxicity/professionalism, and relevance via ML classifiers |
| **Visual (DL)** | Facial expression (CNN), eye contact/gaze, head pose, and posture via pretrained deep learning models |

The three modalities feed a weighted scoring system that produces a unified scorecard with feedback, event timeline, and progress tracking.

---

---

## Member 1 — Amina
### Domain: Visual Deep Learning Pipeline (Computer Vision)

Amina owns the core deep learning visual analysis pipeline — the component that was built specifically for this Deep Learning course. This is the most DL-heavy section of the project.

---

### Algorithms & Components

| Component | Algorithm / Model | Type |
|-----------|------------------|------|
| Face detection & landmarks | **MediaPipe Face Mesh** | Deep learning landmark regression (pretrained) |
| Facial emotion recognition | **FER2013 CNN** (VGG-style, LiteRT) | Convolutional Neural Network (pretrained) |
| Emotion mapping layer | `RAW_TO_INTERVIEW` heuristic mapping | Custom post-processing layer |
| Temporal emotion aggregation | Distribution + dominant class over frames | Statistical aggregation |
| Visual scoring | Weighted mean formula | Configurable weight system |

---

### Deep Learning Concepts to Explain in Viva

1. **Convolutional Neural Networks (CNNs)**
   - What convolution layers do (feature map extraction — edges, textures, facial action units)
   - Pooling layers and why they reduce spatial dimensions
   - Fully-connected head for classification
   - Softmax activation for multi-class probability output
   - Why grayscale 64×64 is used as input (FER2013 format)

2. **Transfer Learning / Pretrained Models**
   - What it means to use a pretrained model (trained on FER2013 dataset, integrated as-is)
   - Why we did NOT train from scratch (data requirement, compute cost)
   - What our contribution is: the pipeline, mapping layer, and aggregation built on top

3. **The FER2013 Dataset**
   - 7 emotion classes: angry, disgust, fear, happy, sad, surprise, neutral
   - Why raw FER classes don't map directly to interview performance
   - The mapping layer design decision (happy → confident, fear/sad/angry → nervous, etc.)

4. **TFLite / LiteRT Inference**
   - Model quantization (the `.tflite` format is a quantized model)
   - Why a quantized model is used (speed, memory, no full TensorFlow dependency in the visual venv)
   - Interpreter setup: allocate tensors → set input → invoke → get output

5. **Temporal Aggregation**
   - Why per-frame predictions are aggregated (single frames are noisy)
   - Dominant class, distribution percentage, emotional stability metric
   - How nervous_expression_frequency and engaged_expression_frequency are computed

6. **Scoring System**
   - Expression score formula: `(confident×1.0 + neutral×0.75 + confused×0.4 + nervous×0.3) / 10`
   - Visual weighted mean: `Σ(wᵢ × scoreᵢ) / Σwᵢ`
   - Configurable VISUAL_WEIGHTS in `config.py`
   - What happens when a modality is missing (weight renormalization)

---

### Files to Study

| File | Why |
|------|-----|
| `backend/ml/visual/emotion_analysis.py` | Core FER2013 CNN integration, mapping layer, per-frame inference |
| `backend/ml/visual/face_analysis.py` | MediaPipe Face Mesh setup, landmark extraction, face crop generation |
| `backend/ml/visual/aggregation.py` | Temporal aggregation logic, all per-metric aggregation functions |
| `backend/ml/visual/scoring.py` | All scoring formulas, weighted mean, `score_expression()` |
| `backend/ml/visual/pipeline.py` | Orchestrator — how all modules are wired together per frame |
| `backend/ml/visual/feedback.py` | How aggregated metrics become actionable feedback messages |
| `backend/ml/visual/frame_processor.py` | Video decoding, frame sampling at ANALYSIS_FPS |
| `backend/config.py` | VISUAL_WEIGHTS, OVERALL_WEIGHTS, ANALYSIS_FPS, MAX_FRAMES |
| `docs/deep-learning.md` | Full methodology document — read this end to end |

---

---

## Member 2 — Zaina
### Domain: Audio / Voice Model + Text Classifiers (Trained ML Models)

Zaina owns all the models that were **trained within this project** from scratch — the TensorFlow audio neural network and the three text-based classifiers. This section covers the full ML training pipeline: feature extraction, model selection, training, evaluation, and inference.

---

### Algorithms & Components

| Component | Algorithm / Model | Type |
|-----------|------------------|------|
| Audio clarity / accent detection | **TensorFlow/Keras Neural Network** (Dense + Dropout) | Neural network — trained from scratch |
| Audio feature extraction | **MFCC, tempo, ZCR, RMS energy** via librosa | Signal processing → feature vector |
| Confidence classification | **Logistic Regression + TF-IDF** pipeline | NLP + linear classifier |
| Professionalism / toxicity detection | **Naive Bayes, Logistic Regression, Random Forest, Gradient Boosting** (best wins) | Ensemble comparison + selection |
| Answer relevance scoring | **TF-IDF Vectorizer + Cosine Similarity** | Vector space model |

---

### Deep Learning Concepts to Explain in Viva

1. **Audio Feature Extraction (MFCC)**
   - What MFCCs (Mel-Frequency Cepstral Coefficients) are and why they represent speech well
   - Mel scale and why it mimics human auditory perception
   - `n_mfcc=40` → 40 coefficients per frame → `np.mean(axis=1)` → 40 scalar features
   - Zero Crossing Rate (ZCR) — measures signal noisiness / voicedness
   - RMS Energy — measures loudness/volume
   - Tempo — speaking rhythm via beat tracking
   - Final feature vector: 40 (MFCC means) + 3 (tempo, ZCR, energy) = **43 features**

2. **Feedforward Neural Network (Dense Layers)**
   - Architecture: `Dense(128, relu) → Dropout(0.3) → Dense(64, relu) → Dropout(0.2) → Dense(1, sigmoid)`
   - ReLU activation and why it's used in hidden layers
   - Sigmoid output for binary classification (English accent = 1, non-English = 0)
   - Binary cross-entropy loss function
   - Adam optimizer (adaptive learning rate)
   - Dropout regularization — what it does and why it prevents overfitting

3. **Training Process**
   - Train/validation split (`validation_split=0.2`)
   - Batch training: `batch_size=32`, `epochs=20`
   - How the model is saved as `.h5` and loaded for inference

4. **TF-IDF Vectorization (Text Models)**
   - Term Frequency × Inverse Document Frequency — what it measures
   - `max_features=5000`, `ngram_range=(1,2)` — unigrams and bigrams
   - Why text must be converted to numbers before any classifier
   - Sparse matrix representation

5. **Multi-Classifier Comparison (Toxicity)**
   - Why four classifiers are trained and compared (Naive Bayes, Logistic Regression, Random Forest, Gradient Boosting)
   - Evaluation metrics: Accuracy, Precision, Recall, F1-score — what each means
   - Why F1-score is used to pick the best model (balances precision and recall on imbalanced data)
   - Class balancing: toxic vs clean samples (2:1 ratio)
   - The final best model is saved as a Pipeline (`TF-IDF + classifier`)

6. **Cosine Similarity (Relevance)**
   - What cosine similarity measures (angle between two vectors, not magnitude)
   - How question and answer are vectorized and compared
   - Why this is better than exact-match for semantic relevance
   - Score scaling: `min(10, similarity × 50 + 3)`

7. **Dataset Knowledge**
   - **Speech Accent Archive** — 2138 MP3 recordings of speakers reading the same passage
   - **SST2 (Stanford Sentiment Treebank)** — sentiment labels mapped to confidence
   - **Jigsaw Toxic Comments** — 150k+ comments labeled for toxicity categories

---

### Files to Study

| File | Why |
|------|-----|
| `backend/classifiers/audio_model.py` | Full audio model: MFCC extraction, Keras architecture, training loop, inference |
| `backend/classifiers/confidence.py` | TF-IDF + Logistic Regression pipeline, SST2 parsing, training and prediction |
| `backend/classifiers/toxicity.py` | Multi-classifier training, comparison, best-model selection, metrics |
| `backend/classifiers/relevance.py` | TF-IDF vectorizer training, cosine similarity scoring |
| `backend/train.py` | Entry point that runs all four training jobs in sequence |
| `backend/models/` | Trained model artifacts: `.h5`, `.pkl` files — understand what each one is |
| `backend/datasets/speech_accent/` | Audio dataset structure (recordings folder + speakers CSV) |
| `backend/datasets/jigsaw/train.csv` | Toxicity dataset structure |
| `backend/config.py` | OVERALL_WEIGHTS (voice 0.30, text 0.35, visual 0.35) |

---

---

## Member 3 — Fatima
### Domain: Gaze / Head Pose + Posture + Auth + API Integration

Fatima owns the remaining visual DL components (gaze estimation and posture analysis), the full authentication system, the Flask API layer, and how all modalities are assembled into the final scorecard. This section covers geometric deep learning applications, security engineering, and system integration.

---

### Algorithms & Components

| Component | Algorithm / Model | Type |
|-----------|------------------|------|
| Eye contact / gaze estimation | **Iris landmark geometry** on MediaPipe Face Mesh | Geometric computation on DL landmarks |
| Head pose estimation | **Perspective-n-Point (solvePnP)** + Rodrigues rotation | 3D geometry on DL landmarks |
| Posture analysis | **MediaPipe Pose (BlazePose)** | Deep learning body landmark regression (pretrained) |
| Overall scorecard assembly | Weighted mean across modalities | Multi-modal fusion |
| Auth — password hashing | **Argon2id** | Cryptographic hashing |
| Auth — sessions & CSRF | **Server-side sessions + double-submit CSRF** | Security pattern |
| Auth — token storage | **SHA-256 hashed tokens** | Secure token storage |

---

### Deep Learning Concepts to Explain in Viva

1. **MediaPipe Face Mesh — Landmark Regression**
   - How Face Mesh is a deep learning model (regresses 478 3D landmark coordinates from a single image)
   - What `refine_landmarks=True` adds: 10 iris landmarks (indices 469–477, 474–477)
   - Why we need landmarks specifically for gaze and head pose (geometric interpretation layer)
   - Coordinate system: normalized `(x, y, z)` converted to pixel coordinates by multiplying by frame width/height

2. **Iris-Based Gaze Estimation (Eye Contact)**
   - How the iris centre is computed: mean of 4 iris landmark coordinates
   - Iris ratio formula: projecting iris position onto the eye's horizontal and vertical axes
   - Why `h_ratio ≈ 0.5` and `v_ratio ≈ 0.5` means looking at camera
   - `GAZE_H_THRESHOLD = 0.22`, `GAZE_V_THRESHOLD = 0.25` as calibrated thresholds
   - Per-frame states and how eye_contact_percentage is calculated

3. **Perspective-n-Point (PnP) — Head Pose**
   - What PnP solves: given known 3D points and their 2D projections, recover the 3D rotation
   - The canonical 3D face model (6 fixed points: nose, chin, eye corners, mouth corners)
   - OpenCV `solvePnP` + `Rodrigues` conversion from rotation vector to rotation matrix
   - Extracting yaw, pitch, roll from the rotation matrix (Euler angles)
   - Event thresholds: `HEAD_YAW_THRESHOLD=30°`, `HEAD_PITCH_DOWN_THRESHOLD=20°`
   - Head stability via **Median Absolute Deviation (MAD)** — why MAD is more robust than std deviation

4. **MediaPipe Pose / BlazePose**
   - BlazePose architecture: two-stage — detection then landmark regression
   - 33 body landmarks with visibility scores
   - Why visibility scores matter: only landmarks with `visibility > 0.5` are trusted
   - Framing-aware design: `body_not_detected` when shoulders not visible → no penalty
   - Shoulder symmetry: `|ls.y - rs.y| / shoulder_width`
   - Head drop: `(shoulder_mid_y - head_y) / shoulder_width` as normalized slouch metric

5. **Multi-Modal Score Fusion**
   - How three independent modality scores (voice /10, text /10, visual /10) are combined
   - Weighted mean with graceful degradation: missing modalities are dropped, weights renormalized
   - `OVERALL_WEIGHTS`: voice 0.30, text 0.35, visual 0.35
   - Why the overall score is still valid even with only one modality present

6. **Authentication & Security (System Design)**
   - Argon2id: memory-hard password hashing, why it's better than bcrypt/SHA
   - `time_cost=3, memory_cost=64MB, parallelism=2` — what these parameters mean
   - Why session tokens are stored as SHA-256 hashes in the DB (token theft mitigation)
   - Double-submit CSRF: HttpOnly session cookie + readable CSRF cookie echoed as header
   - Rate limiting per endpoint to prevent brute-force attacks
   - Account enumeration prevention: generic responses on register/login/forgot

---

### Files to Study

| File | Why |
|------|-----|
| `backend/ml/visual/eye_contact.py` | Iris ratio formula, gaze state classification, eye contact percentage |
| `backend/ml/visual/gaze.py` | solvePnP head pose, Rodrigues decomposition, yaw/pitch/roll, MAD stability |
| `backend/ml/visual/posture.py` | BlazePose setup, shoulder symmetry, head drop, slouch thresholds |
| `backend/ml/visual/scoring.py` | `score_overall()`, all per-metric score functions, `_weighted_mean()` |
| `backend/app.py` | All API endpoints, `_assemble_scorecard()`, multimodal fusion logic |
| `backend/auth/security.py` | Argon2id hashing, token generation, SHA-256 storage, constant-time compare |
| `backend/auth/routes.py` | Full auth flow: register → verify → login → forgot → reset |
| `backend/auth/session.py` | Server-side session lifecycle, cookie management |
| `backend/auth/middleware.py` | `login_required` decorator, CSRF validation, rate limiting |
| `backend/config.py` | All thresholds: GAZE, HEAD_YAW, HEAD_PITCH, POSE, OVERALL_WEIGHTS |
| `backend/utils/assemblyai.py` | AssemblyAI speech-to-text integration |
| `backend/utils/gemini.py` | Groq LLM integration for ideal answer rewriting |

---

---

## Summary Table

| Area | Amina | Zaina | Fatima |
|------|-------|-------|--------|
| **DL Model type** | CNN (FER2013), MediaPipe Face Mesh | TF/Keras Dense NN (trained), TF-IDF classifiers | MediaPipe Pose (BlazePose), geometric DL on landmarks |
| **Training** | Pretrained model integration + mapping layer | Full training pipeline (audio, confidence, toxicity, relevance) | Pretrained model integration + geometric inference |
| **Key DL concept** | CNN architecture, transfer learning, temporal aggregation | MFCC feature extraction, feedforward NN, classifier comparison | PnP / Euler angles, landmark geometry, multi-modal fusion |
| **Non-DL area** | Feedback generation, visual scoring | Dataset preparation, model evaluation metrics | Auth system, API integration, session management |
| **Primary files** | `emotion_analysis.py`, `face_analysis.py`, `aggregation.py`, `scoring.py` | `audio_model.py`, `confidence.py`, `toxicity.py`, `relevance.py`, `train.py` | `eye_contact.py`, `gaze.py`, `posture.py`, `app.py`, `auth/` |

---

## Shared Knowledge (All Members Must Know)

Every member should be able to explain the overall project architecture in case a viva question is broad:

1. **What AceIt does** — multimodal interview coach scoring voice, text, and visual performance
2. **The three modalities** — voice (audio NN), text (ML classifiers), visual (DL pipeline)
3. **The scoring formula** — modality scores /10 combined via weighted mean (`scoring.py`)
4. **Why two virtual environments** — MediaPipe needs `protobuf < 5`, TensorFlow needs `protobuf >= 5.28`; they cannot share a venv → visual pipeline runs as a subprocess (`visual_runner.py`)
5. **Pretrained vs trained from scratch** — visual models are pretrained and integrated; audio model is trained within the project on Speech Accent Archive
6. **The overall data flow** — video upload → frame extraction → face/pose detection → per-frame inference → temporal aggregation → scoring → feedback → scorecard returned to frontend
