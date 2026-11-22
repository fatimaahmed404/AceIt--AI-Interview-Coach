import { useState, useRef, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { analyzeAudio, analyzeFull, saveHistory } from '../api'
import { flattenScorecard } from '../scorecard'

const PROGRESS_STEPS = [
  'Uploading video…',
  'Transcribing audio…',
  'Analyzing facial expressions…',
  'Analyzing eye contact…',
  'Analyzing posture…',
  'Combining results…',
  'Generating feedback…',
]

export default function Record() {
  const { state } = useLocation()
  const question = state?.question || 'Tell me about yourself.'
  const navigate = useNavigate()

  const [phase, setPhase] = useState('IDLE') // IDLE | RECORDING | DONE | ANALYZING
  const [error, setError] = useState('')
  const [progressIdx, setProgressIdx] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const [videoUrl, setVideoUrl] = useState(null)

  const liveVideoRef = useRef(null)
  const playbackRef  = useRef(null)
  const recorderRef  = useRef(null)
  const streamRef    = useRef(null)
  const chunksRef    = useRef([])
  const blobRef      = useRef(null)
  const timerRef     = useRef(null)
  const progTimerRef = useRef(null)

  useEffect(() => () => cleanup(), [])

  const cleanup = () => {
    clearInterval(timerRef.current)
    clearInterval(progTimerRef.current)
    streamRef.current?.getTracks().forEach(t => t.stop())
  }

  const startRecording = async () => {
    setError('')
    let stream
    try {
      // On mobile, prefer the front-facing camera
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' },
        audio: true,
      })
    } catch (err) {
      if (err?.name === 'NotAllowedError') {
        setError('Camera / microphone permission was denied. Please allow access and try again.')
      } else if (err?.name === 'NotFoundError') {
        setError('No camera or microphone was found on this device.')
      } else {
        setError('Could not start the camera. Check your device and browser permissions.')
      }
      return
    }
    streamRef.current = stream
    if (liveVideoRef.current) {
      liveVideoRef.current.srcObject = stream
      liveVideoRef.current.muted = true
      liveVideoRef.current.play().catch(() => {})
    }

    const mime = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4']
      .find(t => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || ''

    let recorder
    try {
      recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream)
    } catch {
      recorder = new MediaRecorder(stream)
    }
    chunksRef.current = []
    recorder.ondataavailable = e => { if (e.data?.size) chunksRef.current.push(e.data) }
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'video/webm' })
      blobRef.current = blob
      setVideoUrl(prev => { if (prev) URL.revokeObjectURL(prev); return URL.createObjectURL(blob) })
      setPhase('DONE')
    }
    recorderRef.current = recorder
    recorder.start(250)
    setPhase('RECORDING')
    setElapsed(0)
    timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000)
  }

  const stopRecording = () => {
    clearInterval(timerRef.current)
    try { recorderRef.current?.stop() } catch { /* noop */ }
    streamRef.current?.getTracks().forEach(t => t.stop())
    if (liveVideoRef.current) liveVideoRef.current.srcObject = null
  }

  const reRecord = () => {
    blobRef.current = null
    setVideoUrl(prev => { if (prev) URL.revokeObjectURL(prev); return null })
    setPhase('IDLE')
    setError('')
  }

  useEffect(() => {
    const el = playbackRef.current
    if (phase === 'DONE' && el && videoUrl) {
      el.srcObject = null
      el.src = videoUrl
      el.load()
    }
  }, [phase, videoUrl])

  const runProgress = () => {
    setProgressIdx(0)
    progTimerRef.current = setInterval(() => {
      setProgressIdx(i => Math.min(i + 1, PROGRESS_STEPS.length - 1))
    }, 1400)
  }

  const handleAnalyze = async () => {
    if (!blobRef.current) return
    setPhase('ANALYZING')
    setError('')
    runProgress()
    try {
      const videoBlob = blobRef.current
      let transcript = ''
      try {
        const audioRes = await analyzeAudio(videoBlob)
        transcript = audioRes.transcript || ''
      } catch { /* best-effort */ }

      const result = await analyzeFull({ videoBlob, question, transcript })
      const session = flattenScorecard(question, transcript, result)
      const saved = await saveHistory(session)
      clearInterval(progTimerRef.current)
      navigate('/results', { state: { ...session, _id: saved.id } })
    } catch (err) {
      clearInterval(progTimerRef.current)
      setPhase('DONE')
      setError(
        err?.status === 401
          ? 'You must be logged in. Please log in and try again.'
          : err?.message?.includes('fetch')
          ? 'Could not reach the server. Make sure the Flask backend is running.'
          : (err?.message || 'Analysis failed. Please try again.')
      )
    }
  }

  const mm = String(Math.floor(elapsed / 60)).padStart(2, '0')
  const ss = String(elapsed % 60).padStart(2, '0')

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: '1.25rem 1rem 2rem' }}>
      <h2 style={{ fontSize: 18, fontWeight: 600, margin: '0 0 4px' }}>Record your answer</h2>
      <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: '0 0 16px' }}>
        Webcam + microphone are analysed together for a full multimodal review.
      </p>

      {/* Question card */}
      <div style={card}>
        <div style={cardHeader}>
          <span style={cardLabel}>Your question</span>
        </div>
        <div style={{ padding: '12px 14px' }}>
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6 }}>{question}</p>
        </div>
      </div>

      {/* Error */}
      {error && <div style={errorBox}>{error}</div>}

      {/* Video area — portrait-friendly on mobile */}
      <div style={{
        background: '#000', borderRadius: 12, overflow: 'hidden', marginBottom: 12,
        border: `1.5px solid ${phase === 'RECORDING' ? '#D94848' : 'var(--color-border-tertiary)'}`,
        position: 'relative',
        /* On mobile use portrait 3:4, on larger screens use 4:3 */
        aspectRatio: '4 / 3',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <video ref={liveVideoRef} playsInline muted
          style={{ width: '100%', height: '100%', objectFit: 'cover',
            display: phase === 'DONE' ? 'none' : 'block' }} />
        <video ref={playbackRef} controls playsInline
          style={{ width: '100%', height: '100%', objectFit: 'contain',
            display: phase === 'DONE' ? 'block' : 'none' }} />

        {phase === 'IDLE' && (
          <div style={{ position: 'absolute', color: '#888', fontSize: 13, textAlign: 'center', padding: '0 20px' }}>
            Camera preview appears here
          </div>
        )}
        {phase === 'RECORDING' && (
          <div style={{ position: 'absolute', top: 10, left: 10, display: 'flex',
            alignItems: 'center', gap: 6, background: 'rgba(0,0,0,0.6)',
            padding: '4px 10px', borderRadius: 20 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#D94848',
              animation: 'pulse 1.2s ease-in-out infinite', display: 'inline-block' }} />
            <span style={{ fontSize: 12, color: '#fff', fontWeight: 500 }}>REC {mm}:{ss}</span>
          </div>
        )}
      </div>

      {/* Controls */}
      {phase === 'IDLE' && (
        <button onClick={startRecording} style={primaryBtn}>
          ● Start recording
        </button>
      )}
      {phase === 'RECORDING' && (
        <button onClick={stopRecording}
          style={{ ...primaryBtn, background: '#FCEBEB', color: '#791F1F', borderColor: '#D94848' }}>
          ■ Stop recording
        </button>
      )}
      {phase === 'DONE' && (
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={reRecord} style={secondaryBtn}>↺ Re-record</button>
          <button onClick={handleAnalyze} style={{ ...primaryBtn, flex: 2 }}>Analyze answer →</button>
        </div>
      )}

      {/* Progress bar */}
      {phase === 'ANALYZING' && (
        <div style={{ ...card, padding: 0 }}>
          <div style={{ padding: '16px 14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <span style={{
                width: 16, height: 16, border: '2px solid #534AB7', borderTopColor: 'transparent',
                borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite',
                flexShrink: 0,
              }} />
              <span style={{ fontSize: 14, fontWeight: 500 }}>{PROGRESS_STEPS[progressIdx]}</span>
            </div>
            <div style={{ height: 6, borderRadius: 3, background: 'var(--color-background-secondary)' }}>
              <div style={{
                width: `${((progressIdx + 1) / PROGRESS_STEPS.length) * 100}%`,
                height: 6, borderRadius: 3, background: '#534AB7', transition: 'width 0.5s ease',
              }} />
            </div>
            <p style={{ margin: '10px 0 0', fontSize: 12, color: 'var(--color-text-secondary)' }}>
              This may take 30–60 seconds depending on video length.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

const card = {
  background: 'var(--color-background-secondary)', borderRadius: 12,
  border: '0.5px solid var(--color-border-tertiary)', overflow: 'hidden', marginBottom: 12,
}
const cardHeader = {
  padding: '8px 14px', borderBottom: '0.5px solid var(--color-border-tertiary)',
}
const cardLabel = { fontSize: 11, color: 'var(--color-text-secondary)' }
const errorBox = {
  background: '#FCEBEB', border: '0.5px solid #F09595', color: '#791F1F',
  borderRadius: 10, padding: '10px 14px', fontSize: 13, marginBottom: 12, lineHeight: 1.5,
}
const primaryBtn = {
  width: '100%', fontSize: 15, padding: '13px 16px', borderRadius: 10, cursor: 'pointer',
  border: '0.5px solid #534AB7', background: '#534AB7', color: '#fff', fontWeight: 500,
  display: 'block',
}
const secondaryBtn = {
  flex: 1, fontSize: 15, padding: '13px 16px', borderRadius: 10, cursor: 'pointer',
  border: '0.5px solid var(--color-border-tertiary)',
  background: 'var(--color-background-primary)', color: 'var(--color-text-primary)',
}
