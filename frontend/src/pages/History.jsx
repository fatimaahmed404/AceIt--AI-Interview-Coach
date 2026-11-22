import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getHistory, deleteSession } from '../api'
import { ScoreBar, scoreColor } from '../components/ui'

export default function History() {
  const [sessions, setSessions] = useState([])
  const [filter, setFilter]     = useState('overall_score')
  const [selected, setSelected] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    getHistory().then(setSessions).catch(() => setSessions([]))
  }, [])

  const handleDelete = async (e, sessionId, index) => {
    e.stopPropagation()
    if (!window.confirm('Delete this session?')) return
    try {
      await deleteSession(sessionId)
      setSessions(prev => prev.filter((_, i) => i !== index))
      if (selected === index) setSelected(null)
    } catch {
      alert('Could not delete session.')
    }
  }

  const sorted = [...sessions].sort((a, b) => (b[filter] || 0) - (a[filter] || 0))

  const filters = [
    { key: 'overall_score', label: 'Overall' },
    { key: 'confidence',    label: 'Confidence' },
    { key: 'eye_contact_score', label: 'Eye contact' },
    { key: 'posture_score', label: 'Posture' },
  ]

  return (
    <div style={{ maxWidth: 740, margin: '0 auto', padding: '1.25rem 1rem 2rem' }}>
      <h2 style={{ fontSize: 18, fontWeight: 600, margin: '0 0 4px' }}>Past sessions</h2>
      <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: '0 0 14px' }}>
        Tap a session to expand details.
      </p>

      {/* Sort filters */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Sort by:</span>
        {filters.map(f => (
          <button key={f.key} onClick={() => setFilter(f.key)} style={{
            fontSize: 13, padding: '6px 12px', borderRadius: 8, cursor: 'pointer',
            border: '0.5px solid',
            borderColor: filter === f.key ? '#534AB7' : 'var(--color-border-tertiary)',
            background: filter === f.key ? '#EEEDFE' : 'var(--color-background-primary)',
            color: filter === f.key ? '#3C3489' : 'var(--color-text-primary)',
            fontWeight: filter === f.key ? 500 : 400,
            minHeight: 36,
          }}>{f.label}</button>
        ))}
      </div>

      {sessions.length === 0 && (
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 14 }}>
          No sessions yet. Record your first answer!
        </p>
      )}

      <div style={{ display: 'grid', gap: 10 }}>
        {sorted.map((s, i) => (
          <div key={s._id || i}
            onClick={() => setSelected(selected === i ? null : i)}
            style={{
              background: 'var(--color-background-secondary)', borderRadius: 12,
              border: `0.5px solid ${selected === i ? '#534AB7' : 'var(--color-border-tertiary)'}`,
              overflow: 'hidden', cursor: 'pointer',
            }}>
            {/* Row header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 14px' }}>
              {/* Score badge */}
              <div style={{
                width: 38, height: 38, borderRadius: 9, flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 600, fontSize: 14,
                background: 'var(--color-background-primary)',
                color: scoreColor(s.overall_score),
              }}>{s.overall_score ?? '–'}</div>

              {/* Title + date */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ margin: 0, fontSize: 13, fontWeight: 500,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {s.question}
                </p>
                <p style={{ margin: 0, fontSize: 11, color: 'var(--color-text-secondary)' }}>
                  {s.date ? new Date(s.date).toLocaleString() : ''}
                </p>
              </div>

              {/* Action buttons */}
              <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                <button onClick={e => { e.stopPropagation(); navigate('/results', { state: s }) }}
                  style={openBtn}>Open</button>
                <button onClick={e => handleDelete(e, s._id, i)}
                  style={delBtn}>✕</button>
              </div>
            </div>

            {/* Expanded detail */}
            {selected === i && (
              <div style={{ borderTop: '0.5px solid var(--color-border-tertiary)', padding: '14px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px,1fr))', gap: 14, marginBottom: 12 }}>
                  <div>
                    <p style={sectionLabel}>Voice & text</p>
                    <ScoreBar label="Confidence"    value={s.confidence} />
                    <ScoreBar label="Relevance"     value={s.relevance} />
                    <ScoreBar label="Professionalism" value={s.professionalism} />
                    <ScoreBar label="Speaking"      value={s.audio_score} />
                  </div>
                  <div>
                    <p style={sectionLabel}>Visual (Deep Learning)</p>
                    <ScoreBar label="Facial expression" value={s.expression_score} />
                    <ScoreBar label="Eye contact"       value={s.eye_contact_score} />
                    <ScoreBar label="Posture"           value={s.posture_score} />
                    <ScoreBar label="Head movement"     value={s.head_movement_score} />
                  </div>
                </div>
                {s.transcript && (
                  <div style={{ background: 'var(--color-background-primary)', borderRadius: 8, padding: '10px 12px' }}>
                    <p style={{ fontSize: 11, color: 'var(--color-text-secondary)', margin: '0 0 4px' }}>
                      Transcript
                    </p>
                    <p style={{ fontSize: 13, lineHeight: 1.6, margin: 0 }}>{s.transcript}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

const sectionLabel = {
  fontSize: 11, fontWeight: 600, color: 'var(--color-text-secondary)', margin: '0 0 8px',
}
const openBtn = {
  fontSize: 12, padding: '6px 12px', borderRadius: 6, cursor: 'pointer',
  background: '#EEEDFE', border: '0.5px solid #534AB7', color: '#3C3489',
  minHeight: 32, flexShrink: 0,
}
const delBtn = {
  fontSize: 13, padding: '6px 10px', borderRadius: 6, cursor: 'pointer',
  background: '#FCEBEB', border: '0.5px solid #F09595', color: '#791F1F',
  minHeight: 32, flexShrink: 0,
}
