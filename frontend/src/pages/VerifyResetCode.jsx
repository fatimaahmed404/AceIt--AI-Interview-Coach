import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { authApi } from '../api'
import { AuthShell, Field, SubmitButton, Alert } from '../auth/authUi'

export default function VerifyResetCode() {
  const location = useLocation()
  const navigate = useNavigate()
  const [email, setEmail] = useState(location.state?.email || '')
  const [code, setCode] = useState('')
  const [alert, setAlert] = useState(null)
  const [loading, setLoading] = useState(false)

  const submit = async (ev) => {
    ev.preventDefault()
    setAlert(null)
    if (!/^\d{6}$/.test(code)) {
      setAlert({ kind: 'error', msg: 'Enter the 6-digit code from your email.' })
      return
    }
    setLoading(true)
    try {
      const res = await authApi.verifyResetCode(email, code)
      navigate('/reset-password', { state: { email, reset_ticket: res.reset_ticket } })
    } catch (err) {
      setAlert({ kind: 'error', msg: err.message || 'Invalid or expired code.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell title="Enter your reset code"
      subtitle="Check your email for a 6-digit code. It expires in 10 minutes."
      footer={<>Didn't get it? <Link to="/forgot-password" style={link}>Request a new code</Link></>}>
      {alert && <Alert kind={alert.kind}>{alert.msg}</Alert>}
      <form onSubmit={submit} noValidate>
        <Field label="Email" name="email" type="email" value={email} onChange={setEmail}
          autoComplete="email" />
        <Field label="6-digit code" name="code" value={code}
          onChange={(v) => setCode(v.replace(/\D/g, '').slice(0, 6))}
          inputMode="numeric" maxLength={6} placeholder="123456" autoFocus />
        <SubmitButton loading={loading}>Verify code</SubmitButton>
      </form>
    </AuthShell>
  )
}

const link = { color: '#534AB7', textDecoration: 'none', fontWeight: 500 }
