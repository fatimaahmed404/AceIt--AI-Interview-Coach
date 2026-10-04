const COLOR_MAP = {
  confidence: '#7F77DD',
  relevance: '#1D9E75',
  professionalism: '#EF9F27',
  audio: '#378ADD',
}

export default function ScoreBar({ label, value, colorKey }) {
  const color = COLOR_MAP[colorKey] || '#888780'
  const pct = Math.min(100, Math.round((value / 10) * 100))

  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 500 }}>{value} / 10</span>
      </div>
      <div style={{
        height: 8, borderRadius: 4,
        background: 'var(--color-background-secondary)'
      }}>
        <div style={{
          width: `${pct}%`, height: 8,
          borderRadius: 4, background: color,
          transition: 'width 0.6s ease'
        }} />
      </div>
    </div>
  )
}