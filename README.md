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

Accounts are protected by a full **authentication system**: email/password
registration with email verification, secure login via server-side sessions
(HttpOnly cookies), password reset by one-time code, and per-user data
ownership so every interview session belongs to exactly one account.

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
| Auth | Argon2id password hashing, server-side sessions (HttpOnly cookie) + CSRF, SMTP email (smtplib) |

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

# ---- Authentication ----
APP_ENV=development                      # "production" forces Secure cookies + HTTPS links
SECRET_KEY=change-me-to-a-long-random-value
FRONTEND_URL=http://localhost:5173       # used in email links; no trailing slash
BACKEND_URL=http://127.0.0.1:5000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
COOKIE_SAMESITE=Lax
COOKIE_SECURE=false                      # true in production (HTTPS)

# ---- SMTP email (verification / password reset) ----
# Leave SMTP_HOST empty to use the dev console fallback (emails are logged,
# never silently reported as sent).
SMTP_HOST=
SMTP_PORT=587
SMTP_SECURE=false                        # true for implicit TLS (port 465)
SMTP_USER=
SMTP_PASS=
MAIL_FROM_NAME=AceIt
MAIL_FROM_ADDRESS=no-reply@aceit.local
```

> The app runs without any of these keys. Transcription (AssemblyAI) and the
> ideal-answer feature (Groq) need their keys; email verification/reset need
> SMTP (or use the console fallback in development — see "Authentication").
> Generate a strong `SECRET_KEY` with:
> `python -c "import secrets; print(secrets.token_urlsafe(48))"`

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
│   ├── auth/                  # authentication (routes, models, sessions, security, email)
│   ├── classifiers/           # baseline ML (confidence, toxicity, relevance, audio)
│   ├── utils/                 # assemblyai (STT), gemini (Groq LLM), email_service/templates
│   ├── ml/visual/             # Deep Learning visual pipeline
│   ├── tests/                 # pytest unit + integration + edge-case tests
│   └── requirements.txt
├── frontend/                  # React + Vite app
│   └── src/
│       ├── auth/              # AuthContext, route guards, auth UI
│       ├── pages/             # Login, Signup, VerifyEmail, Forgot/Reset, Account, …
│       └── components/
└── docs/deep-learning.md      # Deep Learning methodology
```

---

## Authentication

AceIt uses **server-side sessions** rather than tokens in the browser:

- Passwords are hashed with **Argon2id**; only the hash is stored.
- On login the server creates a session record (storing only a SHA-256 hash of
  the opaque session id) and sets two cookies: an **HttpOnly** `aceit_session`
  cookie (not readable by JS) and a readable `aceit_csrf` cookie.
- The SPA echoes the CSRF token in an `X-CSRF-Token` header on every
  state-changing request (**double-submit CSRF** protection). The provided API
  client (`frontend/src/api.js`) does this automatically.
- Nothing sensitive is kept in `localStorage`. On page refresh the app
  re-asks the backend (`GET /api/auth/me`) who the user is.
- Verification tokens and password-reset codes are stored **hashed**, are
  single-use, and expire (24 h for verification, 10 min for the 6-digit reset
  code with an attempt limit).

### Email in development (no SMTP needed)

If `SMTP_HOST` is empty, the email service runs in **console fallback**: the
verification link / reset code is written to the backend log instead of being
sent, and the response reports `"email_delivery": "console"` (it never falsely
claims a real send). To verify an account in dev, copy the `verify-email?token=…`
link from the backend terminal into your browser.

To send real emails, set the SMTP variables. Any provider works — e.g. a
[Mailtrap](https://mailtrap.io/) sandbox inbox for development, or SendGrid /
Mailgun / a Gmail app password for production.

### Account lifecycle

1. **Register** → account created as *pending verification*; a verification
   email is sent.
2. **Verify email** → account becomes *active*; a welcome email is sent once.
3. **Login** → session cookie issued (unverified accounts are blocked and
   offered a resend link).
4. **Forgot password** → 6-digit code emailed → verify code → set new password
   (this revokes all existing sessions and emails a confirmation).
5. **Account settings** → update name, change password, review/sign out
   sessions, or delete the account.

**Account deletion / data retention:** deleting an account permanently removes
the user record and all auth data (sessions, tokens). Past interview sessions
are **anonymised** (their `user_id` is cleared) rather than destroyed, and
recordings were already deleted right after analysis — so no identifiable data
or recordings remain, and nothing is left in an inconsistent state.

---

## API reference (summary)

Public endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | service + visual-pipeline availability |
| GET | `/api/questions` · `/api/questions/<id>` | question bank |
| GET | `/api/model-info` | model metadata + weights |
| GET | `/api/classifier-comparison` | baseline classifier benchmark |

Authentication (`/api/auth`):

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/register` | create account + send verification email |
| POST | `/verify-email` | verify an email token |
| POST | `/resend-verification` | resend verification (cooldown + rate limited) |
| POST | `/login` · `/logout` · `/logout-all` | session login / logout |
| GET | `/me` | current user (`{user:null}` if signed out) |
| POST | `/forgot-password` | email a 6-digit reset code (generic response) |
| POST | `/verify-reset-code` | validate the code, return a reset ticket |
| POST | `/reset-password` | set a new password with the ticket |
| POST | `/change-password` | change password (authenticated) |

Account (`/api/user`, authenticated):

| Method | Path | Purpose |
|--------|------|---------|
| GET/PATCH | `/profile` | view / update profile (name only) |
| GET | `/sessions` | list active sessions |
| DELETE | `/account` | delete account (requires password) |

Protected feature endpoints (authenticated, owner-scoped):

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/analyze` · `/api/analyze-audio` · `/api/analyze-video` · `/api/analyze-full` | analysis |
| POST | `/api/ideal-answer` | LLM ideal answer + comparison |
| GET/POST | `/api/history`, GET `/api/sessions/<id>`, DELETE `/api/history/<id>` | sessions |
| GET | `/api/progress` | trends, averages, streak, strongest/weakest |
| POST | `/api/mock-interview/start` · `/<id>/answer` · `/<id>/complete` | mock flow |

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

The suite includes `tests/test_auth.py` (registration, verification, login,
password reset, authorization/ownership, email service test mode) and
`tests/test_api.py` (protected endpoints with an authenticated client). Tests
run against a throwaway database and use email **console mode**, so no real
accounts or emails are ever used.

### Manually testing the auth flow (dev)

1. Start backend + frontend, open http://localhost:5173, click **Sign up**.
2. Submit the form → the backend log prints a `verify-email?token=…` link
   (console email mode). Open that link in the browser to verify.
3. **Log in**. Record an interview — the session is saved to *your* account.
4. **Forgot password:** on the login page click *Forgot password?*, enter your
   email, read the 6-digit code from the backend log, enter it, set a new
   password, then log in with the new one (the old one is now rejected).
5. **Account settings** (avatar menu → Account settings): change your name or
   password, review sessions, or delete the account.

With real SMTP configured, the emails arrive in your inbox instead of the log.

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
| Can't verify email in dev | copy the `verify-email?token=…` link from the backend log (console email mode) |
| Login stuck / 401 after refresh | ensure the frontend origin is in `CORS_ORIGINS` and `credentials: 'include'` is used (the bundled API client already does) |
| 403 "Invalid CSRF token" | the SPA must send the `aceit_csrf` cookie value as `X-CSRF-Token`; clear cookies and log in again |
| Cookies not set in production | set `APP_ENV=production`, serve over HTTPS, and set `COOKIE_SECURE=true` |

---

## Notes on privacy

Uploaded videos go to `backend/temp_uploads/` and are **deleted after analysis**
by default (`DELETE_VIDEO_AFTER_ANALYSIS=true`). Raw video/audio is not logged.
All visual models are **pretrained** and integrated as-is — feedback is
descriptive, not a psychological assessment.
