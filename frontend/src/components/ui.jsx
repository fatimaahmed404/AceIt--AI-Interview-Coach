/* Reusable presentational components (no external chart libraries). */

export const COLORS = {
  purple: '#534AB7',
  green: '#1D9E75',
  amber: '#EF9F27',
  blue: '#378ADD',
  red: '#D94848',
  teal: '#0F6E56',
}

export function scoreColor(v) {
  if (v == null) return 'var(--color-text-secondary)'
  if (v >= 7.5) return COLORS.green
  if (v >= 5) return COLORS.amber
  return COLORS.red
}

/* Horizontal score bar with label and value. */
export function ScoreBar({ label, value, color }) {
  const v = value == null ? 0 : value
  const c = color || scoreColor(value)
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 500 }}>
          {value == null ? 'N/A' : `${value} / 10`}
        </span>
      </div>
      <div style={{ height: 8, borderRadius: 4, background: 'var(--color-background-secondary)' }}>
        <div style={{
          width: `${Math.min(100, (v / 10) * 100)}%`, height: 8,
          borderRadius: 4, background: c, transition: 'width 0.5s ease',
        }} />
      </div>
    </div>
  )
}

/* Circular score ring for the headline overall score. */
export function ScoreRing({ value, size = 120, label = 'Overall' }) {
  const r = (size - 16) / 2
  const circ = 2 * Math.PI * r
  const pct = value == null ? 0 : Math.min(1, value / 10)
  const color = scoreColor(value)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="var(--color-background-secondary)" strokeWidth={10} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color} strokeWidth={10} strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={circ * (1 - pct)}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }} />
        <text x="50%" y="48%" textAnchor="middle" dominantBaseline="middle"
          style={{ fontSize: size * 0.26, fontWeight: 600, fill: color }}>
          {value == null ? '–' : value}
        </text>
        <text x="50%" y="66%" textAnchor="middle" dominantBaseline="middle"
          style={{ fontSize: size * 0.1, fill: 'var(--color-text-secondary)' }}>
          / 10
        </text>
      </svg>
      <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 4 }}>{label}</span>
    </div>
  )
}

/* Simple SVG line chart for a trend series: [{date, value}]. */
export function TrendChart({ series, color = COLORS.purple, height = 90 }) {
  const data = (series || []).filter(p => p.value != null)
  if (data.length === 0) {
    return <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', padding: '8px 0' }}>
      No data yet
    </div>
  }
  const w = 260
  const pad = 6
  const max = 10
  const stepX = data.length > 1 ? (w - pad * 2) / (data.length - 1) : 0
  const points = data.map((p, i) => {
    const x = pad + i * stepX
    const y = height - pad - (p.value / max) * (height - pad * 2)
    return `${x},${y}`
  }).join(' ')
  const last = data[data.length - 1].value
  return (
    <svg width="100%" viewBox={`0 0 ${w} ${height}`} preserveAspectRatio="none"
      style={{ display: 'block' }}>
      <polyline points={points} fill="none" stroke={color} strokeWidth={2}
        strokeLinejoin="round" strokeLinecap="round" />
      {data.map((p, i) => {
        const x = pad + i * stepX
        const y = height - pad - (p.value / max) * (height - pad * 2)
        return <circle key={i} cx={x} cy={y} r={2.5} fill={color} />
      })}
      <text x={w - pad} y={12} textAnchor="end"
        style={{ fontSize: 11, fontWeight: 600, fill: color }}>{last}</text>
    </svg>
  )
}

/* Card wrapper. */
export function Card({ title, children, accent }) {
  return (
    <div style={{
      background: 'var(--color-background-secondary)', borderRadius: 12,
      border: `0.5px solid ${accent ? accent + '55' : 'var(--color-border-tertiary)'}`,
      overflow: 'hidden', marginBottom: 16,
    }}>
      {title && (
        <div style={{ padding: '10px 16px', borderBottom: '0.5px solid var(--color-border-tertiary)' }}>
          <p style={{ margin: 0, fontSize: 12, fontWeight: 500, color: accent || 'var(--color-text-primary)' }}>
            {title}
          </p>
        </div>
      )}
      <div style={{ padding: '14px 16px' }}>{children}</div>
    </div>
  )
}
