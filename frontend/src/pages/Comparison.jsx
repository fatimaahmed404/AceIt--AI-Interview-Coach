import { useEffect, useState } from 'react'

const COLORS = {
  'Naive Bayes':          { bar: '#7F77DD', bg: '#EEEDFE', text: '#3C3489' },
  'Logistic Regression':  { bar: '#1D9E75', bg: '#E1F5EE', text: '#085041' },
  'Random Forest':        { bar: '#EF9F27', bg: '#FAEEDA', text: '#633806' },
  'Gradient Boosting':    { bar: '#378ADD', bg: '#E6F1FB', text: '#0C447C' },
}

const MetricBar = ({ value, color }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
    <div style={{ flex: 1, height: 8, borderRadius: 4,
      background: 'var(--color-background-secondary)' }}>
      <div style={{ width: `${value}%`, height: 8, borderRadius: 4,
        background: color, transition: 'width 0.6s ease' }} />
    </div>
    <span style={{ fontSize: 12, fontWeight: 500, minWidth: 42 }}>{value}%</span>
  </div>
)

export default function Comparison() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeMetric, setActiveMetric] = useState('accuracy')

  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/classifier-comparison')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div style={{ maxWidth: 700, margin: '3rem auto', padding: '0 1rem',
      color: 'var(--color-text-secondary)' }}>Loading comparison...</div>
  )

  if (!data) return (
    <div style={{ maxWidth: 700, margin: '3rem auto', padding: '0 1rem',
      color: 'var(--color-text-secondary)' }}>Could not load data. Run train.py first.</div>
  )

  const classifiers = Object.keys(COLORS)
  const metrics = ['accuracy', 'precision', 'recall', 'f1']

  return (
    <div style={{ maxWidth: 700, margin: '2rem auto', padding: '0 1rem' }}>
      <h2 style={{ fontSize: 20, fontWeight: 500, marginBottom: 4 }}>
        Classifier comparison
      </h2>
      <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 20 }}>
        Four classifiers trained on the Jigsaw toxicity dataset — professionalism scoring model.
        Best model: <strong>{data.best}</strong>
      </p>

      {/* metric toggle */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {metrics.map(m => (
          <button key={m} onClick={() => setActiveMetric(m)} style={{
            fontSize: 13, padding: '5px 14px', borderRadius: 8, cursor: 'pointer',
            border: '0.5px solid',
            borderColor: activeMetric === m ? '#534AB7' : 'var(--color-border-tertiary)',
            background: activeMetric === m ? '#EEEDFE' : 'var(--color-background-primary)',
            color: activeMetric === m ? '#3C3489' : 'var(--color-text-primary)',
            fontWeight: activeMetric === m ? 500 : 400,
            textTransform: 'capitalize'
          }}>{m === 'f1' ? 'F1 score' : m}</button>
        ))}
      </div>

      {/* classifier cards */}
      <div style={{ display: 'grid', gap: 10, marginBottom: 28 }}>
        {classifiers
          .sort((a, b) => (data[b]?.[activeMetric] || 0) - (data[a]?.[activeMetric] || 0))
          .map((name, rank) => {
            const c = data[name]
            if (!c) return null
            const colors = COLORS[name]
            const isBest = name === data.best
            return (
              <div key={name} style={{
                background: 'var(--color-background-secondary)',
                borderRadius: 12, padding: '14px 16px',
                border: isBest ? `2px solid ${colors.bar}` : '0.5px solid var(--color-border-tertiary)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center',
                  gap: 10, marginBottom: 12 }}>
                  <span style={{ fontSize: 13, fontWeight: 500, color: '#888',
                    minWidth: 20 }}>#{rank + 1}</span>
                  <span style={{ fontSize: 14, fontWeight: 500,
                    flex: 1, color: 'var(--color-text-primary)' }}>{name}</span>
                  {isBest && (
                    <span style={{ fontSize: 11, padding: '3px 10px',
                      borderRadius: 6, background: colors.bg, color: colors.text }}>
                      best model
                    </span>
                  )}
                  <span style={{ fontSize: 16, fontWeight: 500, color: colors.bar }}>
                    {c[activeMetric]}%
                  </span>
                </div>
                <MetricBar value={c[activeMetric]} color={colors.bar} />

                {/* all 4 metrics small */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: 8, marginTop: 12 }}>
                  {metrics.map(m => (
                    <div key={m} style={{ background: 'var(--color-background-primary)',
                      borderRadius: 8, padding: '8px', textAlign: 'center' }}>
                      <p style={{ fontSize: 10, color: 'var(--color-text-secondary)',
                        margin: '0 0 2px', textTransform: 'capitalize' }}>
                        {m === 'f1' ? 'F1' : m}
                      </p>
                      <p style={{ fontSize: 14, fontWeight: 500, margin: 0,
                        color: activeMetric === m ? colors.bar : 'var(--color-text-primary)' }}>
                        {c[m]}%
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
      </div>

      {/* summary table */}
      <div style={{ background: 'var(--color-background-secondary)',
        borderRadius: 12, padding: '1rem', overflowX: 'auto' }}>
        <p style={{ fontSize: 13, fontWeight: 500, margin: '0 0 12px' }}>Summary table</p>
        <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', padding: '6px 8px',
                color: 'var(--color-text-secondary)', fontWeight: 500 }}>Classifier</th>
              {metrics.map(m => (
                <th key={m} style={{ textAlign: 'right', padding: '6px 8px',
                  color: 'var(--color-text-secondary)', fontWeight: 500,
                  textTransform: 'capitalize' }}>{m === 'f1' ? 'F1' : m}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {classifiers.map(name => {
              const c = data[name]
              if (!c) return null
              return (
                <tr key={name} style={{
                  borderTop: '0.5px solid var(--color-border-tertiary)',
                  background: name === data.best ? COLORS[name].bg : 'transparent'
                }}>
                  <td style={{ padding: '8px', fontWeight: name === data.best ? 500 : 400,
                    color: name === data.best ? COLORS[name].text : 'var(--color-text-primary)' }}>
                    {name} {name === data.best ? '★' : ''}
                  </td>
                  {metrics.map(m => (
                    <td key={m} style={{ textAlign: 'right', padding: '8px',
                      color: name === data.best ? COLORS[name].text : 'var(--color-text-primary)' }}>
                      {c[m]}%
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}