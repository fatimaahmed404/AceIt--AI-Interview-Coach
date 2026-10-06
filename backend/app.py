import os
import json
import uuid
import logging
from datetime import datetime, timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId

import config
from classifiers.confidence import predict_confidence
from classifiers.toxicity import predict_toxicity
from classifiers.relevance import predict_relevance
from classifiers.audio_model import predict_audio
from utils.assemblyai import transcribe_audio
from utils.gemini import rewrite_answer, ideal_answer_analysis
from utils.audio_extract import extract_wav
from visual_runner import run_visual_analysis, visual_pipeline_available
from ml.visual.scoring import score_overall
import question_bank

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("aceit.app")

client = MongoClient(config.MONGO_URI)
db = client[config.MONGO_DB]

os.makedirs(config.TEMP_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)

# Seed the question bank on startup (idempotent).
try:
    seeded = question_bank.seed_questions(db)
    log.info("Question bank seeded (%s new).", seeded)
except Exception as exc:  # noqa: BLE001
    log.warning("Could not seed question bank: %s", exc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _serialize(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


def _save_temp_upload(file_storage, suffix):
    name = f"{uuid.uuid4().hex}{suffix}"
    path = os.path.join(config.TEMP_DIR, name)
    file_storage.save(path)
    return path


# ---------------------------------------------------------------------------
# Existing endpoints (unchanged behaviour, kept for backward compatibility)
# ---------------------------------------------------------------------------
@app.route('/api/history', methods=['GET'])
def get_history():
    sessions = list(db.sessions.find({}).sort('date', -1).limit(50))
    for s in sessions:
        s['_id'] = str(s['_id'])
    return jsonify(sessions)


@app.route('/api/history', methods=['POST'])
def save_history():
    data = request.json or {}
    data['date'] = datetime.utcnow().isoformat()
    result = db.sessions.insert_one(data)
    return jsonify({'saved': True, 'id': str(result.inserted_id)})


@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json or {}
    transcript = data.get('transcript') or ''
    question = data.get('question') or ''
    if not transcript.strip():
        return jsonify({'error': 'transcript is required'}), 400

    confidence_score = predict_confidence(transcript)
    toxicity_score = predict_toxicity(transcript)
    relevance_score = predict_relevance(question, transcript)
    rewritten = rewrite_answer(question, transcript)

    return jsonify({
        'confidence': confidence_score,
        'professionalism': toxicity_score,
        'relevance': relevance_score,
        'rewritten_answer': rewritten,
        'overall_score': round(
            (confidence_score + toxicity_score + relevance_score) / 3, 2
        )
    })


@app.route('/api/analyze-audio', methods=['POST'])
def analyze_audio():
    if 'audio' not in request.files:
        return jsonify({'error': "no 'audio' file in request"}), 400
    audio_file = request.files['audio']
    path = _save_temp_upload(audio_file, '.wav')
    try:
        transcript = transcribe_audio(path)
        audio_score = predict_audio(path)
        return jsonify({'transcript': transcript, 'audio_score': audio_score})
    finally:
        if config.DELETE_VIDEO_AFTER_ANALYSIS and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


@app.route('/api/history/<id>', methods=['DELETE'])
def delete_history(id):
    if not id or id == 'undefined':
        return jsonify({'error': 'invalid id'}), 400
    try:
        db.sessions.delete_one({'_id': ObjectId(id)})
        return jsonify({'deleted': True})
    except (InvalidId, Exception) as e:  # noqa: BLE001
        return jsonify({'error': str(e)}), 400


@app.route('/api/classifier-comparison', methods=['GET'])
def classifier_comparison():
    try:
        with open('models/toxicity_comparison.json', 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception:  # noqa: BLE001
        return jsonify({'error': 'Run train.py first'}), 404


# ---------------------------------------------------------------------------
# New: single-session detail
# ---------------------------------------------------------------------------
@app.route('/api/sessions/<id>', methods=['GET'])
def get_session(id):
    try:
        doc = db.sessions.find_one({'_id': ObjectId(id)})
    except (InvalidId, Exception):  # noqa: BLE001
        return jsonify({'error': 'invalid id'}), 400
    if not doc:
        return jsonify({'error': 'session not found'}), 404
    return jsonify(_serialize(doc))


# ---------------------------------------------------------------------------
# New: visual (Deep Learning) analysis of a recorded video
# ---------------------------------------------------------------------------
@app.route('/api/analyze-video', methods=['POST'])
def analyze_video_endpoint():
    """
    Accepts a recorded interview video (multipart field 'video'), runs the
    visual Deep Learning pipeline (facial expression / eye contact / gaze /
    head position / posture) and returns the visual metrics, scores, timeline
    and feedback. The audio/text analysis is handled by the existing endpoints
    and combined client-side (or via /api/analyze-full).
    """
    if 'video' not in request.files:
        return jsonify({'error': "no 'video' file in request"}), 400
    video = request.files['video']
    suffix = os.path.splitext(video.filename or '')[1] or '.webm'
    path = _save_temp_upload(video, suffix)
    try:
        result = run_visual_analysis(path)
        status = 200 if result.get('ok') else 422
        return jsonify(result), status
    finally:
        if config.DELETE_VIDEO_AFTER_ANALYSIS and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# New: full multimodal analysis (audio + text + visual) in one call
# ---------------------------------------------------------------------------
@app.route('/api/analyze-full', methods=['POST'])
def analyze_full():
    """
    One-shot multimodal analysis.

    multipart form fields:
        video     (file, optional)  -> visual DL analysis
        audio     (file, optional)  -> transcription + audio score
        question  (str)
        transcript(str, optional)   -> if provided, skips transcription
    Returns the unified scorecard structure.
    """
    question = request.form.get('question', '')
    transcript = request.form.get('transcript', '') or ''

    video_path = None
    audio_path = None
    extracted_wav = None
    try:
        if 'video' in request.files and request.files['video'].filename:
            v = request.files['video']
            video_path = _save_temp_upload(v, os.path.splitext(v.filename or '')[1] or '.webm')
        if 'audio' in request.files and request.files['audio'].filename:
            a = request.files['audio']
            audio_path = _save_temp_upload(a, '.wav')

        # If no standalone audio was uploaded but we have a video, pull the
        # audio track out of the recording so the voice model can run on it.
        if audio_path is None and video_path is not None:
            extracted_wav = extract_wav(video_path, config.TEMP_DIR)

        # The source used for the audio model + (fallback) transcription.
        audio_source = audio_path or extracted_wav

        # --- Audio / transcription ---
        audio_score = None
        if audio_source:
            try:
                if not transcript.strip():
                    transcript = transcribe_audio(audio_source)
                audio_score = predict_audio(audio_source)
            except Exception as exc:  # noqa: BLE001 - isolate audio failures
                log.warning("Audio analysis failed: %s", exc)

        # --- Text analysis (existing classifiers) ---
        text_block = None
        if transcript.strip():
            try:
                confidence = predict_confidence(transcript)
                professionalism = predict_toxicity(transcript)
                relevance = predict_relevance(question, transcript)
                text_block = {
                    'transcript': transcript,
                    'confidence': confidence,
                    'professionalism': professionalism,
                    'relevance': relevance,
                }
            except Exception as exc:  # noqa: BLE001
                log.warning("Text analysis failed: %s", exc)

        # --- Visual analysis (Deep Learning) ---
        visual_block = None
        if video_path:
            visual_block = run_visual_analysis(video_path)

        response = _assemble_scorecard(question, text_block, audio_score, visual_block)
        return jsonify(response)
    finally:
        # Always clean up the extracted WAV; clean uploads per the privacy setting.
        cleanup = [extracted_wav]
        if config.DELETE_VIDEO_AFTER_ANALYSIS:
            cleanup += [video_path, audio_path]
        for p in cleanup:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


def _assemble_scorecard(question, text_block, audio_score, visual_block):
    """Combine modality results into the unified response format."""
    # Voice sub-score: use the TF audio clarity score as the voice signal.
    voice_score = audio_score

    # Text sub-score: mean of the available text metrics.
    text_score = None
    if text_block:
        vals = [text_block.get('confidence'), text_block.get('professionalism'),
                text_block.get('relevance')]
        vals = [v for v in vals if v is not None]
        if vals:
            text_score = round(sum(vals) / len(vals), 2)

    # Visual sub-score comes straight from the pipeline.
    visual_score = None
    visual_payload = None
    feedback = []
    timeline = []
    if visual_block and visual_block.get('ok'):
        visual_score = visual_block.get('scores', {}).get('score')
        comp = visual_block.get('scores', {}).get('components', {})
        metrics = visual_block.get('metrics', {})
        visual_payload = {
            'facial_expression': {
                'dominant': metrics.get('facial_expression', {}).get('dominant'),
                'confidence': metrics.get('facial_expression', {}).get('confidence'),
                'distribution': metrics.get('facial_expression', {}).get('distribution'),
                'score': comp.get('facial_expression'),
            },
            'eye_contact': {
                'percentage': metrics.get('eye_contact', {}).get('percentage'),
                'score': comp.get('eye_contact'),
            },
            'posture': {
                'good_posture_percentage': metrics.get('posture', {}).get('good_posture_percentage'),
                'score': comp.get('posture'),
            },
            'head_movement': {
                'stability': metrics.get('head_movement', {}).get('stability'),
                'looking_down_frequency': metrics.get('head_movement', {}).get('looking_down_frequency'),
                'score': comp.get('head_movement'),
            },
            'meta': visual_block.get('meta', {}),
        }
        feedback = visual_block.get('feedback', [])
        timeline = visual_block.get('timeline', [])
    elif visual_block and not visual_block.get('ok'):
        visual_payload = {'error': visual_block.get('error')}

    overall = score_overall(voice=voice_score, text=text_score, visual=visual_score)

    return {
        'session_id': uuid.uuid4().hex,
        'question': question,
        'voice': {'audio_score': voice_score, 'score': voice_score} if voice_score is not None else None,
        'text': text_block,
        'visual': visual_payload,
        'overall': {'score': overall},
        'timeline': timeline,
        'feedback': feedback,
    }


# ---------------------------------------------------------------------------
# New: ideal answer analysis
# ---------------------------------------------------------------------------
@app.route('/api/ideal-answer', methods=['POST'])
def ideal_answer():
    data = request.json or {}
    question = data.get('question', '')
    transcript = data.get('transcript', '')
    if not transcript.strip():
        return jsonify({'error': 'transcript is required'}), 400
    return jsonify(ideal_answer_analysis(question, transcript))


# ---------------------------------------------------------------------------
# New: question bank
# ---------------------------------------------------------------------------
@app.route('/api/questions', methods=['GET'])
def get_questions():
    try:
        result = question_bank.query_questions(
            db,
            category=request.args.get('category'),
            subcategory=request.args.get('subcategory'),
            difficulty=request.args.get('difficulty'),
            industry=request.args.get('industry'),
            search=request.args.get('search'),
            limit=int(request.args.get('limit', 100)),
            skip=int(request.args.get('skip', 0)),
        )
        result['categories'] = question_bank.CATEGORIES
        result['technical_subcategories'] = question_bank.TECHNICAL_SUBCATEGORIES
        result['difficulties'] = question_bank.DIFFICULTIES
        return jsonify(result)
    except Exception as exc:  # noqa: BLE001
        return jsonify({'error': str(exc)}), 400


@app.route('/api/questions/<id>', methods=['GET'])
def get_question(id):
    try:
        doc = db.questions.find_one({'_id': ObjectId(id)})
    except (InvalidId, Exception):  # noqa: BLE001
        return jsonify({'error': 'invalid id'}), 400
    if not doc:
        return jsonify({'error': 'question not found'}), 404
    return jsonify(_serialize(doc))


# ---------------------------------------------------------------------------
# New: progress dashboard
# ---------------------------------------------------------------------------
@app.route('/api/progress', methods=['GET'])
def progress():
    sessions = list(db.sessions.find({}).sort('date', 1))
    for s in sessions:
        s['_id'] = str(s['_id'])
    return jsonify(_compute_progress(sessions))


def _compute_progress(sessions):
    """Build trend series, strongest/weakest metric, streak and summary."""
    metric_keys = [
        ('overall_score', 'Overall'),
        ('confidence', 'Confidence'),
        ('relevance', 'Relevance'),
        ('professionalism', 'Professionalism'),
        ('audio_score', 'Speaking pace'),
        ('eye_contact_score', 'Eye contact'),
        ('posture_score', 'Posture'),
        ('expression_score', 'Facial expression'),
    ]
    trends = {key: [] for key, _ in metric_keys}
    for s in sessions:
        date = s.get('date')
        for key, _ in metric_keys:
            val = s.get(key)
            if val is not None:
                trends[key].append({'date': date, 'value': val})

    # Averages across sessions for strongest/weakest (exclude overall).
    averages = {}
    for key, label in metric_keys:
        if key == 'overall_score':
            continue
        vals = [p['value'] for p in trends[key]]
        if vals:
            averages[label] = round(sum(vals) / len(vals), 2)

    strongest = max(averages, key=averages.get) if averages else None
    weakest = min(averages, key=averages.get) if averages else None

    return {
        'total_sessions': len(sessions),
        'trends': trends,
        'averages': averages,
        'strongest_metric': strongest,
        'weakest_metric': weakest,
        'streak': _compute_streak(sessions),
        'recent': [_serialize(dict(s)) for s in sessions[-5:][::-1]],
    }


def _compute_streak(sessions):
    """Consecutive-day practice streak ending today or yesterday."""
    days = set()
    for s in sessions:
        d = s.get('date')
        if not d:
            continue
        try:
            days.add(datetime.fromisoformat(d).date())
        except (ValueError, TypeError):
            continue
    if not days:
        return 0
    today = datetime.utcnow().date()
    # Allow the streak to count from today or yesterday.
    start = today if today in days else (today - timedelta(days=1))
    if start not in days:
        return 0
    streak = 0
    cursor = start
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


# ---------------------------------------------------------------------------
# New: mock interview mode
# ---------------------------------------------------------------------------
@app.route('/api/mock-interview/start', methods=['POST'])
def mock_start():
    """Start a 10-question timed mock interview session."""
    data = request.json or {}
    count = int(data.get('count', 10))
    category = data.get('category')
    query = {'category': category} if category else {}

    pipeline = [{'$match': query}] if query else []
    pipeline.append({'$sample': {'size': count}})
    try:
        questions = list(db.questions.aggregate(pipeline))
    except Exception:  # noqa: BLE001
        questions = list(db.questions.find(query).limit(count))
    for q in questions:
        q['_id'] = str(q['_id'])

    session_doc = {
        'type': 'mock',
        'status': 'in_progress',
        'thinking_time': int(data.get('thinking_time', 30)),
        'questions': questions,
        'answers': [],
        'date': datetime.utcnow().isoformat(),
    }
    result = db.mock_sessions.insert_one(session_doc)
    return jsonify({
        'mock_id': str(result.inserted_id),
        'questions': questions,
        'thinking_time': session_doc['thinking_time'],
        'count': len(questions),
    })


@app.route('/api/mock-interview/<mock_id>/answer', methods=['POST'])
def mock_answer(mock_id):
    """Record a single per-question result inside a mock session."""
    data = request.json or {}
    try:
        oid = ObjectId(mock_id)
    except (InvalidId, Exception):  # noqa: BLE001
        return jsonify({'error': 'invalid mock id'}), 400
    db.mock_sessions.update_one({'_id': oid}, {'$push': {'answers': data}})
    return jsonify({'saved': True})


@app.route('/api/mock-interview/<mock_id>/complete', methods=['POST'])
def mock_complete(mock_id):
    """Finalise a mock session and compute an aggregate report."""
    try:
        oid = ObjectId(mock_id)
    except (InvalidId, Exception):  # noqa: BLE001
        return jsonify({'error': 'invalid mock id'}), 400
    doc = db.mock_sessions.find_one({'_id': oid})
    if not doc:
        return jsonify({'error': 'mock session not found'}), 404

    answers = doc.get('answers', [])
    report = _aggregate_mock(answers)
    db.mock_sessions.update_one(
        {'_id': oid},
        {'$set': {'status': 'completed', 'report': report,
                  'completed_at': datetime.utcnow().isoformat()}},
    )
    return jsonify({'mock_id': mock_id, 'report': report, 'answers': answers})


def _aggregate_mock(answers):
    keys = ['overall_score', 'confidence', 'relevance', 'professionalism',
            'audio_score', 'eye_contact_score', 'posture_score', 'expression_score']
    averages = {}
    for k in keys:
        vals = [a.get(k) for a in answers if a.get(k) is not None]
        if vals:
            averages[k] = round(sum(vals) / len(vals), 2)
    return {
        'questions_answered': len(answers),
        'averages': averages,
        'overall': averages.get('overall_score'),
    }


# ---------------------------------------------------------------------------
# New: model information (DL course requirement)
# ---------------------------------------------------------------------------
@app.route('/api/model-info', methods=['GET'])
def model_info():
    from ml.visual.emotion_analysis import model_info as emotion_info
    from ml.visual.face_analysis import model_info as face_info
    from ml.visual.posture import model_info as pose_info
    return jsonify({
        'visual_pipeline_available': visual_pipeline_available(),
        'models': [emotion_info(), face_info(), pose_info()],
        'weights': {
            'visual': config.VISUAL_WEIGHTS,
            'overall': config.OVERALL_WEIGHTS,
        },
        'analysis_fps': config.ANALYSIS_FPS,
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'visual': visual_pipeline_available()})


if __name__ == '__main__':
    app.run(debug=True)
