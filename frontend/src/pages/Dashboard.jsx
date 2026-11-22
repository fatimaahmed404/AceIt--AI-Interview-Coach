import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getProgress } from '../api'
import { TrendChart, Card, COLORS, scoreColor } from '../components/ui'

const TREND_META = [
  { key: 'overall_score',   label: 'Overall score',    color: COLORS.teal },
  { key: 'eye_contact_score', label: 'Eye contact',    color: COLORS.teal },
  { key: 'posture_score',   label: 'Posture',           color: COLORS.green },
  { key: 'expression_score', label: 'Facial expression', color: COLORS.purple },
  { key: 'confidence',      label: 'Confidence',        color: COLORS.purple },
  { key: 'audio_score',     label: 'Speaking pace',     color: COLORS.blue },
  { key: 'relevance',       label: 'Relevance',         color: COLORS.green },
  { key: 'professionalism', label: 'Professionalism',   color: COLORS.amber },
]

export default function Dashboard() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getProgress().then(setData).catch(() => setData(null)).finally(() => setLoading(false))
  }, [])

  if (loading) return <Centered>Loading progress…</Centered>
  if (!data || data.total_sessions === 0) {
    return (
      <Centered>
        No sessions yet.{' '}
        <button onClick={() => navigate('/')}
          style={{ background: 'none', border: 'none', color: '#534AB7',
                   fontSize: 14, cursor: 'pointer', padding: 0 }}>
          Record an answer
        </button>{' '}
        to start tracking progress.
      </Centered>
    )
  }

  return (
    <div style={{ maxWidth: 820, margin: '0 auto', padding: '1.25rem 1rem 2rem' }}>
      <h2 style={{ fontSize: 18, fontWeight: 600, margin: '0 0 4px' }}>Progress dashboard</h2>
      <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: '0 0 18px' }}>
        Trends across your {data.total_sessions} recorded session{data.total_sessions === 1 ? '' : 's'}.
      </p>

      {/* Summary row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10, marginBottom: 16 }}>
        <SummaryCard label="Practice streak"
          value={`${data.streak} day${data.streak === 1 ? '' : 's'}`} color={COLORS.amber} />
        <SummaryCard label="Total sessions"
          value={data.total_sessions} color={COLORS.blue} />
        <SummaryCard label="Strongest"
          value={data.strongest_metric || '–'} color={COLORS.green} small />
        <SummaryCard label="Needs work"
          value={data.weakest_metric || '–'} color={COLORS.red} small />
      </div>

      {/* Trend charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px,1fr))', gap: 10 }}>
        {TREND_META.map(({ key, label, color }) => {
          const series = data.trends?.[key] || []
          if (series.length === 0) return null
          return (
            <Card key={key} title={label} accent={color}>
              <TrendChart series={series} color={color} />
            </Card>
          )
        })}
      </div>

      {/* Averages */}
      <Card title="Average scores">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px,1fr))', gap: 8 }}>
          {Object.entries(data.averages || {}).map(([label, val]) => (
            <div key={label} style={{
              textAlign: 'center', background: 'var(--color-background-primary)',
              borderRadius: 8, padding: '10px',
            }}>
              <p style={{ margin: 0, fontSize: 11, color: 'var(--color-text-secondary)' }}>{label}</p>
              <p style={{ margin: '4px 0 0', fontSize: 20, fontWeight: 600, color: scoreColor(val) }}>{val}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Recent sessions */}
      <Card title="Recent sessions">
        {(data.recent || []).map(s => (
          <button key={s._id} onClick={() => navigate('/results', { state: s })} style={{
            display: 'flex', alignItems: 'center', gap: 10, width: '100%', textAlign: 'left',
            cursor: 'pointer', background: 'var(--color-background-primary)', marginBottom: 6,
            border: '0.5px solid var(--color-border-tertiary)', borderRadius: 8, padding: '10px 12px',
            minHeight: 'unset',
          }}>
            <span style={{
              width: 36, height: 36, borderRadius: 8, display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontWeight: 600, fontSize: 14, flexShrink: 0,
              background: 'var(--color-background-secondary)', color: scoreColor(s.overall_score),
            }}>{s.overall_score ?? '–'}</span>
            <span style={{ flex: 1, minWidth: 0, fontSize: 13,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {s.question}
            </span>
            <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', flexShrink: 0 }}>
              {s.date ? new Date(s.date).toLocaleDateString() : ''}
            </span>
          </button>
        ))}
      </Card>
    </div>
  )
}

function SummaryCard({ label, value, color, small }) {
  return (
    <div style={{
      background: 'var(--color-background-secondary)', borderRadius: 12,
      padding: '14px 16px', border: '0.5px solid var(--color-border-tertiary)',
    }}>
      <p style={{ margin: 0, fontSize: 11, color: 'var(--color-text-secondary)' }}>{label}</p>
      <p style={{ margin: '4px 0 0', fontSize: small ? 14 : 22, fontWeight: 600, color,
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {value}
      </p>
    </div>
  )
}

function Centered({ children }) {
  return (
    <div style={{ maxWidth: 820, margin: '3rem auto', padding: '0 1rem',
      color: 'var(--color-text-secondary)', fontSize: 14 }}>
      {children}
    </div>
  )
}
