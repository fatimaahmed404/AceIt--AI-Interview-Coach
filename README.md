# AceIt — AI-Powered Interview Coach

AceIt is an AI interview coach. You pick an interview question, record a
**webcam + microphone** answer, and get a **multimodal performance analysis**:

- **Voice** — speaking clarity/pace (TensorFlow audio model)
- **Text** — confidence, professionalism, answer relevancy (ML classifiers) + transcript
- **Visual (Deep Learning)** — facial expression (CNN), eye contact & gaze
  (MediaPipe Face Mesh), head position, and posture (MediaPipe Pose)

Everything is combined into one scorecard with actionable feedback, an event
timeline, an AI "ideal answer", session history, a progress dashboard, and a
timed mock-interview mode.

> The Deep Learning visual pipeline was built for the *Intro to Deep Learning*
> course. Full methodology: [`docs/deep-learning.md`](docs/deep-learning.md).

---

## Tech stack

| Layer | Tech |
|-------|------|
| Frontend | React 19 + Vite |
| Backend | Flask (Python 3.12) |
| Database | MongoDB |
| Baseline ML | scikit-learn, TensorFlow/Keras |
| Deep Learning | MediaPipe (Face Mesh + Pose), FER2013 CNN via LiteRT, OpenCV |
| External APIs | AssemblyAI (speech-to-text), Groq (LLM ideal answer) |

---

## Quick start (setup for your machine)

### 0. Prerequisites

Install these first:
- **Python 3.12**
- **Node.js 18+** and npm
- **MongoDB** running locally (`mongodb://localhost:27017`)
- **ffmpeg** (used for video decoding; also provided via pip packages)

```bash
# Ubuntu/Debian example
sudo apt install python3.12 python3.12-venv nodejs npm mongodb ffmpeg
```

### 1. Clone

```bash
git clone https://github.com/fatimaahmed404/AceIt--AI-Interview-Coach.git
cd AceIt--AI-Interview-Coach
```

### 2. Backend — main environment

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

### 3. Backend — isolated visual (Deep Learning) environment

The visual DL stack lives in a **separate** venv because MediaPipe needs
`protobuf < 5` while TensorFlow needs `protobuf >= 5.28` — they can't share one
environment. Flask runs the visual pipeline as a subprocess using this venv.

```bash
python3 -m venv .venv-visual
.venv-visual/bin/pip install "mediapipe==0.10.14" opencv-python-headless \
    ai-edge-litert av imageio imageio-ffmpeg pytest
.venv-visual/bin/pip install --no-deps fer   # ships the pretrained FER2013 CNN
```

### 4. Configure secrets (`.env`)

API keys live in a git-ignored `.env` file (never committed). Copy the template
and fill in your own keys:

```bash
cp backend/.env.example backend/.env
# then edit backend/.env
```

```ini
MONGO_URI=mongodb://localhost:27017/interview_coach
MONGO_DB=interview_coach
ASSEMBLYAI_API_KEY=your_assemblyai_key   # free: https://www.assemblyai.com/
GROQ_API_KEY=your_groq_key               # free: https://console.groq.com/
GROQ_MODEL=openai/gpt-oss-20b
```

> The app runs without these keys — only transcription (AssemblyAI) and the
> ideal-answer feature (Groq) need them. Everything else works offline.

### 5. Datasets & trained models (not in the repo)

The training **datasets** and generated **model files** are not pushed to
GitHub (too large). To create the baseline models, place the datasets under
`backend/datasets/` (see `train.py` for the expected paths) and run:

```bash
cd backend
../.venv/bin/python train.py
```

This produces `backend/models/*.pkl` and `audio_model.h5`. If you only want to
try the Deep Learning visual features, you can skip training — the visual
pipeline does not depend on these artifacts.

### 6. Frontend

```bash
cd frontend
npm install
```

---

## Running the app

Open two terminals.

**Terminal 1 — backend:**
```bash
cd backend
../.venv/bin/python app.py          # http://127.0.0.1:5000
```

Check it's healthy (should show `"visual": true`):
```bash
curl http://127.0.0.1:5000/api/health
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev                         # http://localhost:5173
```

Open **http://localhost:5173**, pick a question, allow camera/mic, record, and
hit **Analyze**.

> Use `localhost` (not an IP) — browsers only allow webcam/mic access on
> `localhost` or HTTPS.

---

## Project structure

```
AceIt--AI-Interview-Coach/
├── backend/
│   ├── app.py                 # Flask API (all endpoints)
│   ├── config.py              # config + .env loader (keys, weights, thresholds)
│   ├── .env.example           # copy to .env and fill in
│   ├── visual_runner.py       # subprocess bridge to the visual venv
│   ├── question_bank.py       # question seeding + filtered queries
│   ├── classifiers/           # baseline ML (confidence, toxicity, relevance, audio)
│   ├── utils/                 # assemblyai (STT), gemini (Groq LLM)
│   ├── ml/visual/             # Deep Learning visual pipeline
│   ├── tests/                 # pytest unit + integration + edge-case tests
│   └── requirements.txt
├── frontend/                  # React + Vite app (src/pages, src/components)
└── docs/deep-learning.md      # Deep Learning methodology
```

---

## API reference (summary)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | service + visual-pipeline availability |
| POST | `/api/analyze` | text analysis |
| POST | `/api/analyze-audio` | transcription + audio score |
| POST | `/api/analyze-video` | visual DL analysis of a recorded video |
| POST | `/api/analyze-full` | unified multimodal analysis |
| POST | `/api/ideal-answer` | LLM ideal answer + comparison |
| GET | `/api/questions` | question bank (category/subcategory/difficulty/search) |
| GET/POST | `/api/history` | list / save sessions |
| GET | `/api/progress` | trends, averages, streak, strongest/weakest |
| POST | `/api/mock-interview/start` · `/<id>/answer` · `/<id>/complete` | mock flow |
| GET | `/api/model-info` | model metadata + weights |

---

## Testing

```bash
cd backend
# unit + integration (main venv)
../.venv/bin/python -m pytest tests/ --ignore=tests/test_pipeline_edge_cases.py
# visual pipeline edge cases (isolated venv)
../.venv-visual/bin/python -m pytest tests/test_pipeline_edge_cases.py
```

Frontend build check:
```bash
cd frontend && npm run build
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `visual: false` in `/api/health` | `.venv-visual` missing — redo step 3 |
| Transcription fails | set a valid `ASSEMBLYAI_API_KEY` in `backend/.env` |
| Ideal answer missing | set a valid `GROQ_API_KEY` in `backend/.env` |
| `Run train.py first` | run `python train.py` to generate baseline models |
| Mongo connection error | ensure `mongod` is running |
| Webcam not allowed | use `http://localhost`, not an IP address |

---

## Notes on privacy

Uploaded videos go to `backend/temp_uploads/` and are **deleted after analysis**
by default (`DELETE_VIDEO_AFTER_ANALYSIS=true`). Raw video/audio is not logged.
All visual models are **pretrained** and integrated as-is — feedback is
descriptive, not a psychological assessment.
