import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../api'
import { AuthShell, Field, SubmitButton, Alert } from '../auth/authUi'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [alert, setAlert] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const submit = async (ev) => {
    ev.preventDefault()
    setAlert(null)
    setLoading(true)
    try {
      await authApi.forgotPassword(email)
      // Generic response regardless of whether the account exists.
      navigate('/verify-reset-code', { state: { email } })
    } catch (err) {
      setAlert({ kind: 'error', msg: err.message || 'Something went wrong.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell title="Reset your password"
      subtitle="Enter your email and we'll send a 6-digit code to reset your password."
      footer={<>Remembered it? <Link to="/login" style={link}>Back to login</Link></>}>
      {alert && <Alert kind={alert.kind}>{alert.msg}</Alert>}
      <form onSubmit={submit} noValidate>
        <Field label="Email" name="email" type="email" value={email} onChange={setEmail}
          autoComplete="email" placeholder="you@example.com" autoFocus />
        <SubmitButton loading={loading}>Send reset code</SubmitButton>
      </form>
    </AuthShell>
  )
}

const link = { color: '#534AB7', textDecoration: 'none', fontWeight: 500 }
