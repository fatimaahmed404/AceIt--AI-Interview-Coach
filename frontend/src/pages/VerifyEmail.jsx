import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { authApi } from '../api'
import { AuthShell, Field, SubmitButton, Alert } from '../auth/authUi'

export default function VerifyEmail() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const [state, setState] = useState(token ? 'verifying' : 'manual') // verifying|success|error|manual
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const [resendMsg, setResendMsg] = useState(null)
  const navigate = useNavigate()
  const ran = useRef(false)

  useEffect(() => {
    if (!token || ran.current) return
    ran.current = true
    ;(async () => {
      try {
        const res = await authApi.verifyEmail(token)
        setState('success'); setMessage(res.message || 'Email verified.')
      } catch (err) {
        setState('error'); setMessage(err.message || 'Verification failed.')
      }
    })()
  }, [token])

  const resend = async (ev) => {
    ev.preventDefault()
    setResendMsg(null)
    try {
      await authApi.resendVerification(email)
      setResendMsg('If that account exists and is unverified, a new link has been sent.')
    } catch (err) {
      setResendMsg(err.message || 'Could not resend.')
    }
  }

  if (state === 'verifying') {
    return <AuthShell title="Verifying your email…" subtitle="One moment." />
  }
  if (state === 'success') {
    return (
      <AuthShell title="Email verified" subtitle={message}
        footer={<>You can now <Link to="/login" style={link}>log in</Link>.</>}>
        <Alert kind="success">Your account is active. Welcome to AceIt!</Alert>
        <button onClick={() => navigate('/login')} style={primaryBtn}>Continue to login</button>
      </AuthShell>
    )
  }
  if (state === 'error') {
    return (
      <AuthShell title="Verification failed" subtitle={message}
        footer={<>Back to <Link to="/login" style={link}>login</Link></>}>
        <Alert kind="error">{message}</Alert>
        <form onSubmit={resend}>
          <Field label="Resend verification to" name="email" type="email" value={email}
            onChange={setEmail} autoComplete="email" placeholder="you@example.com" />
          <SubmitButton>Resend verification email</SubmitButton>
        </form>
        {resendMsg && <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 10 }}>{resendMsg}</p>}
      </AuthShell>
    )
  }
  // manual (no token in URL)
  return (
    <AuthShell title="Verify your email"
      subtitle="Open the verification link we emailed you, or request a new one below."
      footer={<>Back to <Link to="/login" style={link}>login</Link></>}>
      <form onSubmit={resend}>
        <Field label="Email" name="email" type="email" value={email} onChange={setEmail}
          autoComplete="email" placeholder="you@example.com" autoFocus />
        <SubmitButton>Resend verification email</SubmitButton>
      </form>
      {resendMsg && <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 10 }}>{resendMsg}</p>}
    </AuthShell>
  )
}

const link = { color: '#534AB7', textDecoration: 'none', fontWeight: 500 }
const primaryBtn = { width: '100%', fontSize: 14, padding: '11px 16px', borderRadius: 8,
  cursor: 'pointer', border: '0.5px solid #534AB7', background: '#534AB7', color: '#fff', fontWeight: 500 }
