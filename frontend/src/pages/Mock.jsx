import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { startMock, submitMockAnswer, completeMock, analyzeAudio, analyzeFull } from '../api'
import { flattenScorecard } from '../scorecard'
import { ScoreRing, Card, COLORS, scoreColor } from '../components/ui'

// Phases: SETUP -> THINKING -> RECORDING -> PROCESSING -> (next) -> REPORT
export default function Mock() {
  const [phase, setPhase] = useState('SETUP')
  const [mock, setMock] = useState(null)
  const [idx, setIdx] = useState(0)
  const [think, setThink] = useState(30)
  const [countdown, setCountdown] = useState(0)
  const [report, setReport] = useState(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  const liveRef = useRef(null)
  const streamRef = useRef(null)
  const recorderRef = useRef(null)
  const chunksRef = useRef([])
  const timerRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => () => stopStream(), [])

  const stopStream = () => {
    clearInterval(timerRef.current)
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop())
  }

  const begin = async () => {
    setError('')
    const data = await startMock({ count: 10, thinking_time: think }).catch(() => null)
    if (!data || !data.questions?.length) {
      setError('Could not start the mock interview. Is the backend running?')
      return
    }
    setMock(data)
    setIdx(0)
    await enterThinking(0)
  }

  const enterThinking = async (questionIdx) => {
    setPhase('THINKING')
    setCountdown(think)
    // open camera early so the preview is ready
    try {
      streamRef.current = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      if (liveRef.current) { liveRef.current.srcObject = streamRef.current; liveRef.current.muted = true; liveRef.current.play().catch(() => {}) }
    } catch {
      setError('Camera/microphone permission is required for a mock interview.')
      setPhase('SETUP'); return
    }
    clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      setCountdown(c => {
        if (c <= 1) { clearInterval(timerRef.current); startRecording(); return 0 }
        return c - 1
      })
    }, 1000)
  }

  const startRecording = () => {
    if (!streamRef.current) return
    const mime = ['video/webm;codecs=vp8,opus', 'video/webm'].find(t => MediaRecorder.isTypeSupported(t)) || 'video/webm'
    const rec = new MediaRecorder(streamRef.current, { mimeType: mime })
    chunksRef.current = []
    rec.ondataavailable = e => { if (e.data?.size) chunksRef.current.push(e.data) }
    rec.onstop = () => processAnswer(new Blob(chunksRef.current, { type: 'video/webm' }))
    recorderRef.current = rec
    rec.start()
    setPhase('RECORDING')
  }

  const stopRecording = () => {
    try { recorderRef.current?.stop() } catch { /* noop */ }
  }

  const processAnswer = async (videoBlob) => {
    setPhase('PROCESSING')
    setStatus('Analyzing answer…')
    const question = mock.questions[idx].text
    let transcript = ''
    try { transcript = (await analyzeAudio(videoBlob)).transcript || '' } catch { /* best effort */ }
    let result = null
    try { result = await analyzeFull({ videoBlob, question, transcript }) } catch { /* noop */ }
    const flat = flattenScorecard(question, transcript, result || {})
    await submitMockAnswer(mock.mock_id, flat).catch(() => {})

    const next = idx + 1
    if (next >= mock.questions.length) {
      setStatus('Building report…')
      const res = await completeMock(mock.mock_id).catch(() => null)
      stopStream()
      setReport(res?.report || null)
      setPhase('REPORT')
    } else {
      setIdx(next)
      await enterThinking(next)
    }
  }

  // ---- renders ----
  if (phase === 'SETUP') {
    return (
      <Wrap>
        <h2 style={h2}>Mock interview</h2>
        <p style={sub}>Ten questions, one at a time, timed, with no redo — just like the real thing.</p>
        {error && <ErrorBox>{error}</ErrorBox>}
        <Card title="Settings">
          <label style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>
            Thinking time per question: <strong>{think}s</strong>
          </label>
          <input type="range" min="5" max="60" step="5" value={think}
            onChange={e => setThink(Number(e.target.value))} style={{ width: '100%' }} />
          <ul style={{ fontSize: 12.5, color: 'var(--color-text-secondary)', lineHeight: 1.7, marginTop: 12 }}>
            <li>Recording starts automatically after the thinking time.</li>
            <li>You cannot re-record an answer during the mock.</li>
            <li>A full session scorecard is shown at the end.</li>
          </ul>
        </Card>
        <button onClick={begin} style={primaryBtn}>Start mock interview →</button>
      </Wrap>
    )
  }

  if (phase === 'REPORT') {
    const avg = report?.averages || {}
    return (
      <Wrap>
        <h2 style={h2}>Mock interview complete</h2>
        <p style={sub}>You answered {report?.questions_answered ?? 0} questions.</p>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
          <ScoreRing value={report?.overall} size={140} label="Session score" />
        </div>
        <Card title="Average scores">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px,1fr))', gap: 10 }}>
            {Object.entries(avg).map(([k, v]) => (
              <div key={k} style={{ textAlign: 'center', background: 'var(--color-background-primary)', borderRadius: 8, padding: '10px' }}>
                <p style={{ margin: 0, fontSize: 11, color: 'var(--color-text-secondary)' }}>{labelFor(k)}</p>
                <p style={{ margin: '2px 0 0', fontSize: 20, fontWeight: 600, color: scoreColor(v) }}>{v}</p>
              </div>
            ))}
          </div>
        </Card>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={() => navigate('/dashboard')} style={primaryBtn}>View dashboard</button>
          <button onClick={() => { setPhase('SETUP'); setReport(null) }} style={secondaryBtn}>Run again</button>
        </div>
      </Wrap>
    )
  }

  // THINKING / RECORDING / PROCESSING
  const q = mock?.questions[idx]
  return (
    <Wrap>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontSize: 13, fontWeight: 500 }}>Question {idx + 1} of {mock?.questions.length}</span>
        <span style={{ fontSize: 13, color: COLORS.purple }}>{labelPhase(phase)}</span>
      </div>
      <div style={{ height: 5, borderRadius: 3, background: 'var(--color-background-secondary)', marginBottom: 14 }}>
        <div style={{ width: `${((idx) / mock.questions.length) * 100}%`, height: 5, borderRadius: 3, background: COLORS.purple }} />
      </div>

      <Card accent={COLORS.purple}>
        <p style={{ margin: 0, fontSize: 15, lineHeight: 1.6 }}>{q?.text}</p>
      </Card>

      <div style={{ background: '#000', borderRadius: 12, overflow: 'hidden', aspectRatio: '4 / 3',
        position: 'relative', marginBottom: 14, border: `1px solid ${phase === 'RECORDING' ? '#D94848' : 'var(--color-border-tertiary)'}` }}>
        <video ref={liveRef} playsInline muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        {phase === 'THINKING' && (
          <div style={overlay}>
            <div style={{ fontSize: 42, fontWeight: 700, color: '#fff' }}>{countdown}</div>
            <div style={{ fontSize: 13, color: '#ddd' }}>Think about your answer…</div>
          </div>
        )}
        {phase === 'RECORDING' && (
          <div style={{ position: 'absolute', top: 10, left: 10, background: 'rgba(0,0,0,0.55)', padding: '4px 10px', borderRadius: 20 }}>
            <span style={{ fontSize: 12, color: '#fff' }}>● REC</span>
          </div>
        )}
        {phase === 'PROCESSING' && <div style={overlay}><div style={{ fontSize: 14, color: '#fff' }}>{status}</div></div>}
      </div>

      {phase === 'RECORDING' && <button onClick={stopRecording} style={{ ...primaryBtn, background: '#FCEBEB', color: '#791F1F', border: '0.5px solid #D94848' }}>■ Stop & submit</button>}
      {phase === 'THINKING' && <button onClick={() => { clearInterval(timerRef.current); startRecording() }} style={secondaryBtn}>Skip prep, start now</button>}
    </Wrap>
  )
}

const labelPhase = p => ({ THINKING: 'Preparing', RECORDING: 'Recording', PROCESSING: 'Analyzing' }[p] || '')
const labelFor = k => ({
  overall_score: 'Overall', confidence: 'Confidence', relevance: 'Relevance',
  professionalism: 'Professionalism', audio_score: 'Speaking', eye_contact_score: 'Eye contact',
  posture_score: 'Posture', expression_score: 'Expression',
}[k] || k)

const Wrap = ({ children }) => <div style={{ maxWidth: 640, margin: '2rem auto', padding: '0 1rem' }}>{children}</div>
const ErrorBox = ({ children }) => <div style={{ background: '#FCEBEB', border: '0.5px solid #F09595', color: '#791F1F', borderRadius: 10, padding: '10px 14px', fontSize: 13, marginBottom: 14 }}>{children}</div>
const overlay = { position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 6, background: 'rgba(0,0,0,0.4)' }
const h2 = { fontSize: 20, fontWeight: 500, marginBottom: 4 }
const sub = { fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 20 }
const primaryBtn = { flex: 2, width: '100%', fontSize: 14, padding: '11px 16px', borderRadius: 8, cursor: 'pointer', border: '0.5px solid #534AB7', background: '#534AB7', color: '#fff', fontWeight: 500 }
const secondaryBtn = { flex: 1, width: '100%', fontSize: 14, padding: '11px 16px', borderRadius: 8, cursor: 'pointer', border: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-secondary)', color: 'var(--color-text-primary)' }
