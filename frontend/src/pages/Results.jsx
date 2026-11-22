import { useLocation, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { getIdealAnswer } from '../api'
import { ScoreRing, ScoreBar, Card, COLORS, scoreColor } from '../components/ui'

const EVENT_LABELS = {
  looking_left: 'Looking left', looking_right: 'Looking right',
  looking_up: 'Looking up', looking_down: 'Looking down',
  good_eye_contact: 'Good eye contact', face_not_detected: 'Face not detected',
  turned_away: 'Head turned away', head_tilt: 'Head tilt', slouch_detected: 'Slouch detected',
}

function fmtTime(t) {
  const m = Math.floor(t / 60)
  const s = Math.floor(t % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function Results() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const [ideal, setIdeal] = useState(null)
  const [idealLoading, setIdealLoading] = useState(false)

  useEffect(() => {
    if (state?.transcript) {
      setIdealLoading(true)
      getIdealAnswer(state.question, state.transcript)
        .then(setIdeal)
        .catch(() => setIdeal(null))
        .finally(() => setIdealLoading(false))
    }
  }, [state])

  if (!state) { navigate('/'); return null }

  const {
    question, transcript, overall_score,
    confidence, professionalism, relevance, audio_score,
    eye_contact_percentage, eye_contact_score,
    posture_percentage, posture_score,
    expression_dominant, expression_score,
    head_stability, head_movement_score,
    timeline = [], feedback = [], visual_error,
  } = state

  const hasVisual = eye_contact_score != null || posture_score != null ||
    expression_score != null || head_movement_score != null

  return (
    <div style={{ maxWidth: 760, margin: '2rem auto', padding: '0 1rem' }}>
      <h2 style={{ fontSize: 20, fontWeight: 500, marginBottom: 2 }}>Your results</h2>
      <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 20 }}>{question}</p>

      {/* Overall header */}
      <div style={{
        display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap',
        background: 'var(--color-background-secondary)', borderRadius: 12, padding: '18px 20px',
        border: '0.5px solid var(--color-border-tertiary)', marginBottom: 16,
      }}>
        <ScoreRing value={overall_score} />
        <div style={{ flex: 1, minWidth: 200 }}>
          <p style={{ margin: '0 0 10px', fontSize: 13, fontWeight: 500 }}>Overall performance</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px,1fr))', gap: 8 }}>
            <MiniStat label="Voice" value={audio_score} />
            <MiniStat label="Confidence" value={confidence} />
            <MiniStat label="Relevance" value={relevance} />
            <MiniStat label="Eye contact" value={eye_contact_score} />
          </div>
        </div>
      </div>

      {/* Voice + Text */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px,1fr))', gap: 12 }}>
        <Card title="Voice analysis" accent={COLORS.blue}>
          <ScoreBar label="Speaking / audio clarity" value={audio_score} color={COLORS.blue} />
          <p style={subtle}>Clarity and delivery estimated by the audio model.</p>
        </Card>
        <Card title="Text analysis" accent={COLORS.green}>
          <ScoreBar label="Confidence" value={confidence} color={COLORS.purple} />
          <ScoreBar label="Professionalism" value={professionalism} color={COLORS.amber} />
          <ScoreBar label="Answer relevancy" value={relevance} color={COLORS.green} />
        </Card>
      </div>

      {/* Visual / Deep Learning */}
      <Card title="Visual / Deep Learning analysis" accent={COLORS.purple}>
        {visual_error && (
          <p style={{ fontSize: 13, color: '#791F1F' }}>Visual analysis note: {visual_error}</p>
        )}
        {!hasVisual && !visual_error && (
          <p style={subtle}>No visual metrics were available for this session.</p>
        )}
        {hasVisual && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px,1fr))', gap: 8, marginBottom: 14 }}>
              <MetricTile label="Facial expression" score={expression_score}
                sub={expression_dominant ? `dominant: ${expression_dominant}` : ''} />
              <MetricTile label="Eye contact" score={eye_contact_score}
                sub={eye_contact_percentage != null ? `${eye_contact_percentage}% at camera` : ''} />
              <MetricTile label="Posture" score={posture_score}
                sub={posture_percentage != null ? `${posture_percentage}% upright` : ''} />
              <MetricTile label="Head movement" score={head_movement_score}
                sub={head_stability != null ? `stability ${head_stability}` : ''} />
            </div>
            <ScoreBar label="Facial expression" value={expression_score} color={COLORS.purple} />
            <ScoreBar label="Eye contact" value={eye_contact_score} color={COLORS.teal} />
            <ScoreBar label="Posture" value={posture_score} color={COLORS.green} />
            <ScoreBar label="Head movement" value={head_movement_score} color={COLORS.blue} />
          </>
        )}
      </Card>

      {/* Timeline */}
      {timeline.length > 0 && (
        <Card title="Timeline" accent={COLORS.amber}>
          <Timeline timeline={timeline} />
        </Card>
      )}

      {/* Feedback */}
      {feedback.length > 0 && (
        <Card title="Actionable feedback" accent={COLORS.teal}>
          {feedback.map((f, i) => (
            <div key={i} style={{ marginBottom: 10, paddingBottom: 10,
              borderBottom: i < feedback.length - 1 ? '0.5px solid var(--color-border-tertiary)' : 'none' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                <span style={{ fontSize: 12, fontWeight: 500, color: COLORS.teal }}>{f.category}</span>
                {f.score != null && <span style={{ fontSize: 12, color: scoreColor(f.score) }}>{f.score}/10</span>}
              </div>
              <p style={{ margin: 0, fontSize: 13, lineHeight: 1.6 }}>{f.message}</p>
            </div>
          ))}
        </Card>
      )}

      {/* Transcript + ideal answer */}
      <Card title="Transcript">
        <p style={{ fontSize: 13, lineHeight: 1.7, margin: 0 }}>
          {transcript || <span style={subtle}>No transcript available.</span>}
        </p>
      </Card>

      <Card title="AI suggested (ideal) answer" accent={COLORS.purple}>
        {idealLoading && <p style={subtle}>Generating ideal answer…</p>}
        {!idealLoading && ideal && (
          <>
            <p style={{ fontSize: 13, lineHeight: 1.7, margin: '0 0 12px', color: '#26215C',
              background: '#EEEDFE', padding: '12px', borderRadius: 8 }}>
              {ideal.ideal_answer}
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px,1fr))', gap: 10 }}>
              <FeedbackList title="What you did well" items={ideal.did_well} color={COLORS.green} />
              <FeedbackList title="What to improve" items={ideal.improve} color={COLORS.amber} />
              <FeedbackList title="Missing points" items={ideal.missing_points} color={COLORS.blue} />
              <FeedbackList title="Areas to avoid" items={ideal.avoid} color={COLORS.red} />
            </div>
          </>
        )}
        {!idealLoading && !ideal && <p style={subtle}>Ideal answer unavailable.</p>}
      </Card>

      <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
        <button onClick={() => navigate('/')} style={btn}>Try another question</button>
        <button onClick={() => navigate('/history')} style={btn}>View history</button>
        <button onClick={() => navigate('/dashboard')} style={btn}>Progress dashboard</button>
      </div>
    </div>
  )
}

function Timeline({ timeline }) {
  const videoSeek = (t) => {
    const v = document.querySelector('video')
    if (v) { v.currentTime = t; v.scrollIntoView({ behavior: 'smooth', block: 'center' }) }
  }
  return (
    <div style={{ display: 'grid', gap: 6 }}>
      {timeline.filter(e => e.event !== 'good_eye_contact').slice(0, 25).map((e, i) => (
        <button key={i} onClick={() => videoSeek(e.timestamp)} style={{
          display: 'flex', alignItems: 'center', gap: 10, textAlign: 'left', cursor: 'pointer',
          background: 'var(--color-background-primary)', border: '0.5px solid var(--color-border-tertiary)',
          borderRadius: 8, padding: '6px 10px',
        }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: COLORS.purple, minWidth: 44 }}>
            {fmtTime(e.timestamp)}
          </span>
          <span style={{ fontSize: 13 }}>{EVENT_LABELS[e.event] || e.event}</span>
          {e.duration > 0 && <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginLeft: 'auto' }}>
            {e.duration}s
          </span>}
        </button>
      ))}
    </div>
  )
}

function FeedbackList({ title, items, color }) {
  if (!items || items.length === 0) return null
  return (
    <div>
      <p style={{ fontSize: 11, fontWeight: 600, color, margin: '0 0 6px' }}>{title}</p>
      <ul style={{ margin: 0, paddingLeft: 16 }}>
        {items.map((it, i) => <li key={i} style={{ fontSize: 12.5, lineHeight: 1.6, marginBottom: 2 }}>{it}</li>)}
      </ul>
    </div>
  )
}

function MiniStat({ label, value }) {
  return (
    <div>
      <p style={{ margin: 0, fontSize: 11, color: 'var(--color-text-secondary)' }}>{label}</p>
      <p style={{ margin: 0, fontSize: 18, fontWeight: 600, color: scoreColor(value) }}>
        {value == null ? '–' : value}
      </p>
    </div>
  )
}

function MetricTile({ label, score, sub }) {
  return (
    <div style={{ background: 'var(--color-background-primary)', borderRadius: 8, padding: '10px', textAlign: 'center' }}>
      <p style={{ margin: 0, fontSize: 11, color: 'var(--color-text-secondary)' }}>{label}</p>
      <p style={{ margin: '2px 0', fontSize: 20, fontWeight: 600, color: scoreColor(score) }}>
        {score == null ? '–' : score}
      </p>
      {sub && <p style={{ margin: 0, fontSize: 10, color: 'var(--color-text-secondary)' }}>{sub}</p>}
    </div>
  )
}

const subtle = { fontSize: 12, color: 'var(--color-text-secondary)', margin: 0 }
const btn = {
  flex: 1, fontSize: 13, padding: '9px 16px', borderRadius: 8, cursor: 'pointer',
  border: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-secondary)',
  color: 'var(--color-text-primary)',
}
