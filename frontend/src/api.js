const BASE = 'http://127.0.0.1:5000/api'

// ---------------------------------------------------------------------------
// Core request helpers
//
// The backend uses server-side sessions via an HttpOnly cookie, so every
// request must send credentials. State-changing requests (POST/PUT/PATCH/
// DELETE) to protected endpoints must also echo the CSRF token from the
// (non-HttpOnly) aceit_csrf cookie in the X-CSRF-Token header (double-submit).
// ---------------------------------------------------------------------------
function getCookie(name) {
  const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'))
  return m ? decodeURIComponent(m[1]) : null
}

function csrfHeader() {
  const token = getCookie('aceit_csrf')
  return token ? { 'X-CSRF-Token': token } : {}
}

/** JSON request with credentials + CSRF. Throws { status, data } on non-2xx. */
async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const isWrite = method !== 'GET' && method !== 'HEAD'
  const res = await fetch(`${BASE}${path}`, {
    method,
    credentials: 'include',
    headers: {
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...(isWrite ? csrfHeader() : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  let data = null
  try { data = await res.json() } catch { /* empty body */ }
  if (!res.ok) {
    const err = new Error((data && data.error) || `Request failed (${res.status})`)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

/** Multipart (file upload) request with credentials + CSRF. */
async function upload(path, formData) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    credentials: 'include',
    headers: { ...csrfHeader() },
    body: formData,
  })
  let data = null
  try { data = await res.json() } catch { /* empty */ }
  if (!res.ok) {
    const err = new Error((data && data.error) || `Request failed (${res.status})`)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

// ===========================================================================
// Authentication
// ===========================================================================
export const authApi = {
  me: () => request('/auth/me'),
  register: (payload) => request('/auth/register', { method: 'POST', body: payload }),
  login: (payload) => request('/auth/login', { method: 'POST', body: payload }),
  logout: () => request('/auth/logout', { method: 'POST', body: {} }),
  logoutAll: () => request('/auth/logout-all', { method: 'POST', body: {} }),
  verifyEmail: (token) => request('/auth/verify-email', { method: 'POST', body: { token } }),
  resendVerification: (email) =>
    request('/auth/resend-verification', { method: 'POST', body: { email } }),
  forgotPassword: (email) =>
    request('/auth/forgot-password', { method: 'POST', body: { email } }),
  verifyResetCode: (email, code) =>
    request('/auth/verify-reset-code', { method: 'POST', body: { email, code } }),
  resetPassword: (payload) =>
    request('/auth/reset-password', { method: 'POST', body: payload }),
  changePassword: (payload) =>
    request('/auth/change-password', { method: 'POST', body: payload }),
}

export const userApi = {
  getProfile: () => request('/user/profile'),
  updateProfile: (payload) => request('/user/profile', { method: 'PATCH', body: payload }),
  listSessions: () => request('/user/sessions'),
  deleteAccount: (password) =>
    request('/user/account', { method: 'DELETE', body: { password } }),
}

// ===========================================================================
// Existing feature API (now credential + CSRF aware)
// ===========================================================================
export const analyzeAudio = async (audioBlob) => {
  const fd = new FormData()
  fd.append('audio', audioBlob, 'recording.wav')
  return upload('/analyze-audio', fd)
}

export const analyzeText = (question, transcript) =>
  request('/analyze', { method: 'POST', body: { question, transcript } })

export const getHistory = () => request('/history')

export const saveHistory = (data) => request('/history', { method: 'POST', body: data })

export const deleteSession = (id) => request(`/history/${id}`, { method: 'DELETE' })

export const analyzeVideo = async (videoBlob) => {
  const fd = new FormData()
  fd.append('video', videoBlob, 'recording.webm')
  return upload('/analyze-video', fd)
}

export const analyzeFull = async ({ videoBlob, audioBlob, question, transcript }) => {
  const fd = new FormData()
  if (videoBlob) fd.append('video', videoBlob, 'recording.webm')
  if (audioBlob) fd.append('audio', audioBlob, 'recording.wav')
  if (question) fd.append('question', question)
  if (transcript) fd.append('transcript', transcript)
  return upload('/analyze-full', fd)
}

export const getIdealAnswer = (question, transcript) =>
  request('/ideal-answer', { method: 'POST', body: { question, transcript } })

export const getProgress = () => request('/progress')

export const getQuestions = async (params = {}) => {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v != null && v !== '')
  ).toString()
  return request(`/questions${qs ? `?${qs}` : ''}`)
}

export const startMock = ({ count = 10, category = null, thinking_time = 30 } = {}) =>
  request('/mock-interview/start', { method: 'POST', body: { count, category, thinking_time } })

export const submitMockAnswer = (mockId, data) =>
  request(`/mock-interview/${mockId}/answer`, { method: 'POST', body: data })

export const completeMock = (mockId) =>
  request(`/mock-interview/${mockId}/complete`, { method: 'POST', body: {} })

export const getModelInfo = () => request('/model-info')
