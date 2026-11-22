import { useEffect, useState } from 'react'
import { getModelInfo } from '../api'
import { Card, COLORS } from '../components/ui'

export default function ModelInfo() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getModelInfo().then(setData).catch(() => setData(null)).finally(() => setLoading(false))
  }, [])

  if (loading) return <Wrap><p style={sub}>Loading model information…</p></Wrap>
  if (!data) return <Wrap><p style={sub}>Could not load model info. Is the backend running?</p></Wrap>

  return (
    <Wrap>
      <h2 style={{ fontSize: 20, fontWeight: 500, marginBottom: 4 }}>Model information</h2>
      <p style={sub}>
        The Deep Learning visual pipeline uses pretrained models. We integrate them; we do not
        claim to have trained them from scratch.
      </p>

      <div style={{
        display: 'inline-block', fontSize: 12, padding: '4px 12px', borderRadius: 6, marginBottom: 16,
        background: data.visual_pipeline_available ? '#E1F5EE' : '#FAEEDA',
        color: data.visual_pipeline_available ? '#0F6E56' : '#BA7517',
      }}>
        Visual pipeline: {data.visual_pipeline_available ? 'available' : 'unavailable'} · analysis FPS {data.analysis_fps}
      </div>

      {(data.models || []).map((m, i) => (
        <Card key={i} title={m.name} accent={COLORS.purple}>
          <Row k="Library" v={m.library} />
          <Row k="Type" v={m.type} />
          <Row k="Pretrained" v={m.pretrained ? 'Yes (integrated as-is)' : 'No'} />
          <Row k="Trained from scratch" v={m.trained_from_scratch ? 'Yes' : 'No'} />
          <Row k="Input" v={m.input} />
          <Row k="Output" v={m.output} />
          {m.raw_classes && <Row k="Raw classes" v={m.raw_classes.join(', ')} />}
          {m.interview_mapping && (
            <div style={{ marginTop: 8 }}>
              <p style={{ fontSize: 12, fontWeight: 500, margin: '0 0 4px' }}>Emotion mapping layer</p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px,1fr))', gap: 4 }}>
                {Object.entries(m.interview_mapping).map(([raw, mapped]) => (
                  <span key={raw} style={{ fontSize: 11.5, color: 'var(--color-text-secondary)' }}>
                    {raw} → <strong style={{ color: 'var(--color-text-primary)' }}>{mapped}</strong>
                  </span>
                ))}
              </div>
            </div>
          )}
          {m.used_for && <Row k="Used for" v={m.used_for.join(', ')} />}
        </Card>
      ))}

      <Card title="Scoring weights">
        <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', margin: '0 0 8px' }}>
          Visual sub-scores combine into one visual score; the three modalities combine into the overall score.
          All weights are configurable in backend/config.py.
        </p>
        <Row k="Visual weights" v={JSON.stringify(data.weights?.visual)} />
        <Row k="Overall weights" v={JSON.stringify(data.weights?.overall)} />
      </Card>
    </Wrap>
  )
}

const Row = ({ k, v }) => (
  <div style={{ display: 'flex', gap: 10, marginBottom: 4 }}>
    <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', minWidth: 140 }}>{k}</span>
    <span style={{ fontSize: 12.5 }}>{v}</span>
  </div>
)
const Wrap = ({ children }) => <div style={{ maxWidth: 700, margin: '2rem auto', padding: '0 1rem' }}>{children}</div>
const sub = { fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }
