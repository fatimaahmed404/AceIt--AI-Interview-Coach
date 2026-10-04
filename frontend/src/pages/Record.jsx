import { useState, useRef, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { analyzeAudio, analyzeFull, saveHistory } from '../api'
import { flattenScorecard } from '../scorecard'

// UX states: IDLE -> RECORDING -> UPLOADING/ANALYZING -> (navigate to RESULT)
const PROGRESS_STEPS = [
  'Uploading video...',
  'Transcribing audio...',
  'Analyzing facial expressions...',
  'Analyzing eye contact...',
  'Analyzing posture...',
  'Combining results...',
  'Generating feedback...',
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
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const blobRef = useRef(null)
  const timerRef = useRef(null)
  const progTimerRef = useRef(null)

  useEffect(() => () => cleanup(), [])

  const cleanup = () => {
    clearInterval(timerRef.current)
    clearInterval(progTimerRef.current)
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop())
  }

  const startRecording = async () => {
    setError('')
    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    } catch (err) {
      if (err && err.name === 'NotAllowedError') {
        setError('Camera / microphone permission was denied. Please allow access and try again.')
      } else if (err && err.name === 'NotFoundError') {
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

    // Pick a widely supported container.
    const mime = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm']
      .find(t => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || 'video/webm'

    let recorder
    try {
      recorder = new MediaRecorder(stream, { mimeType: mime })
    } catch {
      recorder = new MediaRecorder(stream)
    }
    chunksRef.current = []
    recorder.ondataavailable = (e) => { if (e.data && e.data.size) chunksRef.current.push(e.data) }
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: 'video/webm' })
      blobRef.current = blob
      setVideoUrl(URL.createObjectURL(blob))
      setPhase('DONE')
    }
    recorderRef.current = recorder
    recorder.start()
    setPhase('RECORDING')
    setElapsed(0)
    timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000)
  }

  const stopRecording = () => {
    clearInterval(timerRef.current)
    try { recorderRef.current?.stop() } catch { /* noop */ }
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop())
  }

  const reRecord = () => {
    blobRef.current = null
    setVideoUrl(null)
    setPhase('IDLE')
    setError('')
  }

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
      // Transcribe audio track from the same recording (reuse existing endpoint).
      let transcript = ''
      try {
        const audioRes = await analyzeAudio(videoBlob)
        transcript = audioRes.transcript || ''
      } catch { /* transcription is best-effort; analyze-full will retry */ }

      const result = await analyzeFull({ videoBlob, question, transcript })

      // Flatten into the session shape used by History / Results / Progress.
      const session = flattenScorecard(question, transcript, result)
      const saved = await saveHistory(session)
      clearInterval(progTimerRef.current)
      navigate('/results', { state: { ...session, _id: saved.id } })
    } catch {
      clearInterval(progTimerRef.current)
      setPhase('DONE')
      setError('Analysis failed. Make sure the Flask backend is running on port 5000.')
    }
  }

  const mm = String(Math.floor(elapsed / 60)).padStart(2, '0')
  const ss = String(elapsed % 60).padStart(2, '0')

  return (
    <div style={{ maxWidth: 640, margin: '2.5rem auto', padding: '0 1rem' }}>
      <h2 style={{ fontSize: 20, fontWeight: 500, marginBottom: 4 }}>Record your answer</h2>
      <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 20 }}>
        Your webcam and microphone are analysed together for a full multimodal review.
      </p>

      {/* Question */}
      <div style={{
        background: 'var(--color-background-secondary)', borderRadius: 12,
        border: '0.5px solid var(--color-border-tertiary)', overflow: 'hidden', marginBottom: 16,
      }}>
        <div style={{ padding: '10px 16px', borderBottom: '0.5px solid var(--color-border-tertiary)' }}>
          <p style={{ margin: 0, fontSize: 11, color: 'var(--color-text-secondary)' }}>Your question</p>
        </div>
        <div style={{ padding: '12px 16px' }}>
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6 }}>{question}</p>
        </div>
      </div>

      {error && (
        <div style={{
          background: '#FCEBEB', border: '0.5px solid #F09595', color: '#791F1F',
          borderRadius: 10, padding: '10px 14px', fontSize: 13, marginBottom: 16,
        }}>{error}</div>
      )}

      {/* Video stage */}
      <div style={{
        background: '#000', borderRadius: 12, overflow: 'hidden', marginBottom: 16,
        border: `1px solid ${phase === 'RECORDING' ? '#D94848' : 'var(--color-border-tertiary)'}`,
        aspectRatio: '4 / 3', position: 'relative', display: 'flex', alignItems: 'center',
        justifyContent: 'center',
      }}>
        {/* Live preview while idle/recording, playback when done */}
        {phase === 'DONE' && videoUrl ? (
          <video src={videoUrl} controls style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
        ) : (
          <video ref={liveVideoRef} playsInline muted
            style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        )}

        {phase === 'IDLE' && (
          <div style={{ position: 'absolute', color: '#ccc', fontSize: 13 }}>
            Camera preview appears here
          </div>
        )}
        {phase === 'RECORDING' && (
          <div style={{
            position: 'absolute', top: 10, left: 10, display: 'flex', alignItems: 'center',
            gap: 6, background: 'rgba(0,0,0,0.55)', padding: '4px 10px', borderRadius: 20,
          }}>
            <span style={{ width: 9, height: 9, borderRadius: '50%', background: '#D94848',
              animation: 'pulse 1.2s ease-in-out infinite' }} />
            <span style={{ fontSize: 12, color: '#fff' }}>REC {mm}:{ss}</span>
          </div>
        )}
      </div>
      <style>{`@keyframes pulse {0%{opacity:1}50%{opacity:.3}100%{opacity:1}}`}</style>

      {/* Controls */}
      {phase === 'IDLE' && (
        <button onClick={startRecording} style={primaryBtn}>● Start recording</button>
      )}
      {phase === 'RECORDING' && (
        <button onClick={stopRecording} style={{ ...primaryBtn, background: '#FCEBEB', color: '#791F1F', border: '0.5px solid #D94848' }}>
          ■ Stop recording
        </button>
      )}
      {phase === 'DONE' && (
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={reRecord} style={secondaryBtn}>↺ Re-record</button>
          <button onClick={handleAnalyze} style={{ ...primaryBtn, flex: 2 }}>Analyze answer →</button>
        </div>
      )}

      {phase === 'ANALYZING' && (
        <div style={{
          background: 'var(--color-background-secondary)', borderRadius: 12,
          border: '0.5px solid var(--color-border-tertiary)', padding: '18px 16px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <span className="spinner" style={{
              width: 16, height: 16, border: '2px solid #534AB7', borderTopColor: 'transparent',
              borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite',
            }} />
            <span style={{ fontSize: 14, fontWeight: 500 }}>{PROGRESS_STEPS[progressIdx]}</span>
          </div>
          <div style={{ height: 6, borderRadius: 3, background: 'var(--color-background-primary)' }}>
            <div style={{
              width: `${((progressIdx + 1) / PROGRESS_STEPS.length) * 100}%`, height: 6,
              borderRadius: 3, background: '#534AB7', transition: 'width 0.5s ease',
            }} />
          </div>
          <style>{`@keyframes spin {to {transform: rotate(360deg)}}`}</style>
        </div>
      )}
    </div>
  )
}

const primaryBtn = {
  width: '100%', fontSize: 14, padding: '11px 16px', borderRadius: 8, cursor: 'pointer',
  border: '0.5px solid #534AB7', background: '#534AB7', color: '#fff', fontWeight: 500,
}
const secondaryBtn = {
  flex: 1, fontSize: 14, padding: '11px 16px', borderRadius: 8, cursor: 'pointer',
  border: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-primary)',
  color: 'var(--color-text-primary)', fontWeight: 400,
}
