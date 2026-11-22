import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getQuestions } from '../api'

const CATEGORY_META = {
  HR: { color: '#EF9F27', bg: '#FAEEDA', text: '#BA7517' },
  Behavioural: { color: '#7F77DD', bg: '#EEEDFE', text: '#26215C' },
  Technical: { color: '#1D9E75', bg: '#E1F5EE', text: '#0F6E56' },
  Situational: { color: '#378ADD', bg: '#E6F1FB', text: '#0C447C' },
}

// Fallback used only if the backend is unreachable.
const FALLBACK = [
  { text: 'Tell me about yourself.', category: 'HR', difficulty: 'Easy' },
  { text: 'Describe a challenge you overcame.', category: 'Behavioural', difficulty: 'Medium' },
  { text: 'How does a binary search tree work?', category: 'Technical', difficulty: 'Medium' },
]

export default function Home() {
  const [category, setCategory] = useState('HR')
  const [subcategory, setSubcategory] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [search, setSearch] = useState('')
  const [questions, setQuestions] = useState([])
  const [selected, setSelected] = useState('')
  const [meta, setMeta] = useState({ categories: Object.keys(CATEGORY_META), technical_subcategories: [], difficulties: [] })
  const [loading, setLoading] = useState(true)
  const [offline, setOffline] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    let active = true
    setLoading(true)
    getQuestions({ category, subcategory, difficulty, search, limit: 200 })
      .then(data => {
        if (!active) return
        const list = data.questions || []
        setQuestions(list)
        setMeta(m => ({
          categories: data.categories || m.categories,
          technical_subcategories: data.technical_subcategories || [],
          difficulties: data.difficulties || [],
        }))
        setSelected(list[0]?.text || '')
        setOffline(false)
      })
      .catch(() => {
        if (!active) return
        const list = FALLBACK.filter(q => q.category === category)
        setQuestions(list.length ? list : FALLBACK)
        setSelected((list[0] || FALLBACK[0]).text)
        setOffline(true)
      })
      .finally(() => active && setLoading(false))
    return () => { active = false }
  }, [category, subcategory, difficulty, search])

  const cmeta = CATEGORY_META[category] || CATEGORY_META.HR

  const shuffle = () => {
    if (questions.length) setSelected(questions[Math.floor(Math.random() * questions.length)].text)
  }

  return (
    <div style={{ maxWidth: 640, margin: '2.5rem auto', padding: '0 1rem' }}>
      <h2 style={{ fontSize: 20, fontWeight: 500, marginBottom: 4 }}>Interview practice</h2>
      <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 20 }}>
        Pick a question, record a webcam answer, get a full multimodal review.
      </p>

      {/* Category tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        {meta.categories.map(cat => {
          const m = CATEGORY_META[cat] || CATEGORY_META.HR
          const active = category === cat
          return (
            <button key={cat} onClick={() => { setCategory(cat); setSubcategory('') }} style={{
              fontSize: 13, padding: '5px 14px', borderRadius: 8, cursor: 'pointer', border: '0.5px solid',
              borderColor: active ? m.color : 'var(--color-border-tertiary)',
              background: active ? m.bg : 'var(--color-background-primary)',
              color: active ? m.text : 'var(--color-text-primary)', fontWeight: active ? 500 : 400,
            }}>{cat}</button>
          )
        })}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        {category === 'Technical' && (
          <select value={subcategory} onChange={e => setSubcategory(e.target.value)} style={selectStyle}>
            <option value="">All topics</option>
            {meta.technical_subcategories.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        )}
        <select value={difficulty} onChange={e => setDifficulty(e.target.value)} style={selectStyle}>
          <option value="">Any difficulty</option>
          {meta.difficulties.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search questions…"
          style={{ ...selectStyle, flex: 1, minWidth: 140 }} />
      </div>

      {/* Question select */}
      <div style={{ background: 'var(--color-background-secondary)', borderRadius: 12,
        border: '0.5px solid var(--color-border-tertiary)', overflow: 'hidden', marginBottom: 10 }}>
        <div style={{ padding: '10px 16px', borderBottom: '0.5px solid var(--color-border-tertiary)',
          display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>Select question</span>
          <span style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
            {loading ? 'Loading…' : `${questions.length} available`}
          </span>
        </div>
        <div style={{ padding: '12px 16px' }}>
          <select value={selected} onChange={e => setSelected(e.target.value)} style={{ ...selectStyle, width: '100%' }}>
            {questions.length === 0 && <option>No questions match these filters</option>}
            {questions.map((q, i) => (
              <option key={i} value={q.text}>{q.text.length > 72 ? q.text.slice(0, 72) + '…' : q.text}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Selected display */}
      {selected && (
        <div style={{ background: cmeta.bg, borderRadius: 12, border: `0.5px solid ${cmeta.color}33`,
          padding: '14px 16px', marginBottom: 10 }}>
          <p style={{ margin: '0 0 4px', fontSize: 11, color: cmeta.color, fontWeight: 500 }}>{category} question</p>
          <p style={{ margin: 0, fontSize: 14, color: cmeta.text, lineHeight: 1.6 }}>{selected}</p>
        </div>
      )}

      {offline && (
        <p style={{ fontSize: 11, color: '#BA7517', marginBottom: 10 }}>
          Backend offline — showing a small offline question set.
        </p>
      )}

      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={shuffle} style={secondaryBtn}>Shuffle ↺</button>
        <button onClick={() => navigate('/record', { state: { question: selected } })}
          disabled={!selected} style={{ ...primaryBtn, opacity: selected ? 1 : 0.5 }}>
          Start recording →
        </button>
      </div>
    </div>
  )
}

const selectStyle = {
  fontSize: 13, padding: '7px 10px', borderRadius: 8, border: '0.5px solid var(--color-border-tertiary)',
  background: 'var(--color-background-primary)', color: 'var(--color-text-primary)', cursor: 'pointer',
}
const primaryBtn = {
  flex: 2, fontSize: 13, padding: '9px 16px', borderRadius: 8, cursor: 'pointer',
  border: '0.5px solid #534AB7', background: '#534AB7', color: '#fff', fontWeight: 500,
}
const secondaryBtn = {
  flex: 1, fontSize: 13, padding: '9px 16px', borderRadius: 8, cursor: 'pointer',
  border: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-secondary)',
  color: 'var(--color-text-primary)',
}
