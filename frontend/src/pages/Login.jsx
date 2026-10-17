import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { authApi } from '../api'
import { useAuth } from '../auth/AuthContext'
import { AuthShell, Field, SubmitButton, Alert } from '../auth/authUi'

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '', remember: false })
  const [alert, setAlert] = useState(null)
  const [needsVerification, setNeedsVerification] = useState(false)
  const [resendMsg, setResendMsg] = useState(null)
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const set = (k) => (v) => setForm(f => ({ ...f, [k]: v }))
  const dest = location.state?.from || '/'

  const submit = async (ev) => {
    ev.preventDefault()
    setAlert(null); setNeedsVerification(false); setResendMsg(null)
    setLoading(true)
    try {
      await login(form.email, form.password, form.remember)
      navigate(dest, { replace: true })
    } catch (err) {
      if (err.status === 403 && err.data?.needs_verification) {
        setNeedsVerification(true)
        setAlert({ kind: 'info', msg: 'Please verify your email before logging in.' })
      } else {
        setAlert({ kind: 'error', msg: err.message || 'Login failed.' })
      }
    } finally {
      setLoading(false)
    }
  }

  const resend = async () => {
    setResendMsg(null)
    try {
      await authApi.resendVerification(form.email)
      setResendMsg('If that account exists and is unverified, a new link has been sent.')
    } catch (err) {
      setResendMsg(err.message || 'Could not resend verification email.')
    }
  }

  return (
    <AuthShell title="Welcome back" subtitle="Log in to continue practicing."
      footer={<>New to AceIt? <Link to="/signup" style={linkStyle}>Create an account</Link></>}>
      {alert && <Alert kind={alert.kind}>{alert.msg}</Alert>}
      {needsVerification && (
        <div style={{ marginBottom: 16 }}>
          <button type="button" onClick={resend} style={secondaryBtn}>Resend verification email</button>
          {resendMsg && <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 6 }}>{resendMsg}</p>}
        </div>
      )}
      <form onSubmit={submit} noValidate>
        <Field label="Email" name="email" type="email" value={form.email}
          onChange={set('email')} autoComplete="email" autoFocus />
        <Field label="Password" name="password" type="password" value={form.password}
          onChange={set('password')} autoComplete="current-password" />
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5,
                          color: 'var(--color-text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" checked={form.remember} onChange={(e) => set('remember')(e.target.checked)}
              style={{ accentColor: '#534AB7' }} />
            Remember me
          </label>
          <Link to="/forgot-password" style={{ ...linkStyle, fontSize: 12.5 }}>Forgot password?</Link>
        </div>
        <SubmitButton loading={loading}>Log in</SubmitButton>
      </form>
    </AuthShell>
  )
}

const linkStyle = { color: '#534AB7', textDecoration: 'none', fontWeight: 500 }
const secondaryBtn = { width: '100%', fontSize: 13, padding: '9px 16px', borderRadius: 8,
  cursor: 'pointer', border: '0.5px solid var(--color-border-tertiary)',
  background: 'var(--color-background-primary)', color: 'var(--color-text-primary)' }
