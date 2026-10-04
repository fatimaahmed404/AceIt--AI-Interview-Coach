const BASE = 'http://127.0.0.1:5000/api'

// ---- existing (preserved) ----
export const analyzeAudio = async (audioBlob) => {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.wav')
  const res = await fetch(`${BASE}/analyze-audio`, { method: 'POST', body: formData })
  return res.json()
}

export const analyzeText = async (question, transcript) => {
  const res = await fetch(`${BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, transcript }),
  })
  return res.json()
}

export const getHistory = async () => {
  const res = await fetch(`${BASE}/history`)
  return res.json()
}

export const saveHistory = async (data) => {
  const res = await fetch(`${BASE}/history`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return res.json()
}

export const deleteSession = async (id) => {
  await fetch(`${BASE}/history/${id}`, { method: 'DELETE' })
}

// ---- new: Deep Learning visual analysis ----
export const analyzeVideo = async (videoBlob) => {
  const formData = new FormData()
  formData.append('video', videoBlob, 'recording.webm')
  const res = await fetch(`${BASE}/analyze-video`, { method: 'POST', body: formData })
  return res.json()
}

// Full multimodal analysis in a single call (video + audio + text).
export const analyzeFull = async ({ videoBlob, audioBlob, question, transcript }) => {
  const formData = new FormData()
  if (videoBlob) formData.append('video', videoBlob, 'recording.webm')
  if (audioBlob) formData.append('audio', audioBlob, 'recording.wav')
  if (question) formData.append('question', question)
  if (transcript) formData.append('transcript', transcript)
  const res = await fetch(`${BASE}/analyze-full`, { method: 'POST', body: formData })
  return res.json()
}

// ---- new: ideal answer ----
export const getIdealAnswer = async (question, transcript) => {
  const res = await fetch(`${BASE}/ideal-answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, transcript }),
  })
  return res.json()
}

// ---- new: progress dashboard ----
export const getProgress = async () => {
  const res = await fetch(`${BASE}/progress`)
  return res.json()
}

// ---- new: question bank ----
export const getQuestions = async (params = {}) => {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v != null && v !== '')
  ).toString()
  const res = await fetch(`${BASE}/questions${qs ? `?${qs}` : ''}`)
  return res.json()
}

// ---- new: mock interview ----
export const startMock = async ({ count = 10, category = null, thinking_time = 30 } = {}) => {
  const res = await fetch(`${BASE}/mock-interview/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ count, category, thinking_time }),
  })
  return res.json()
}

export const submitMockAnswer = async (mockId, data) => {
  const res = await fetch(`${BASE}/mock-interview/${mockId}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return res.json()
}

export const completeMock = async (mockId) => {
  const res = await fetch(`${BASE}/mock-interview/${mockId}/complete`, { method: 'POST' })
  return res.json()
}

// ---- new: model info ----
export const getModelInfo = async () => {
  const res = await fetch(`${BASE}/model-info`)
  return res.json()
}
