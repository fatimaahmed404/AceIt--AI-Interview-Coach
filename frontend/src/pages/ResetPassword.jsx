import { useState } from 'react'
import { Link, useNavigate, useLocation, Navigate } from 'react-router-dom'
import { authApi } from '../api'
import { AuthShell, Field, PasswordStrength, SubmitButton, Alert } from '../auth/authUi'

export default function ResetPassword() {
  const location = useLocation()
  const navigate = useNavigate()
  const email = location.state?.email
  const ticket = location.state?.reset_ticket
  const [pw, setPw] = useState('')
  const [confirm, setConfirm] = useState('')
  const [alert, setAlert] = useState(null)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  // If the user landed here without completing the previous step, send them back.
  if (!email || !ticket) return <Navigate to="/forgot-password" replace />

  const submit = async (ev) => {
    ev.preventDefault()
    setAlert(null)
    if (pw.length < 12) { setAlert({ kind: 'error', msg: 'Password must be at least 12 characters.' }); return }
    if (pw !== confirm) { setAlert({ kind: 'error', msg: 'Passwords do not match.' }); return }
    setLoading(true)
    try {
      await authApi.resetPassword({ email, reset_ticket: ticket, new_password: pw, confirm_password: confirm })
      setDone(true)
    } catch (err) {
      setAlert({ kind: 'error', msg: err.message || 'Could not reset password.' })
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <AuthShell title="Password updated"
        subtitle="Your password has been changed. For security, all sessions were signed out."
        footer={<>Back to <Link to="/login" style={link}>login</Link></>}>
        <Alert kind="success">You can now log in with your new password.</Alert>
        <button onClick={() => navigate('/login')} style={primaryBtn}>Go to login</button>
      </AuthShell>
    )
  }

  return (
    <AuthShell title="Set a new password" subtitle={`Choose a new password for ${email}.`}
      footer={<>Back to <Link to="/login" style={link}>login</Link></>}>
      {alert && <Alert kind={alert.kind}>{alert.msg}</Alert>}
      <form onSubmit={submit} noValidate>
        <Field label="New password" name="new_password" type="password" value={pw}
          onChange={setPw} autoComplete="new-password" autoFocus />
        <PasswordStrength password={pw} />
        <Field label="Confirm new password" name="confirm_password" type="password" value={confirm}
          onChange={setConfirm} autoComplete="new-password" />
        <SubmitButton loading={loading}>Update password</SubmitButton>
      </form>
    </AuthShell>
  )
}

const link = { color: '#534AB7', textDecoration: 'none', fontWeight: 500 }
const primaryBtn = { width: '100%', fontSize: 14, padding: '11px 16px', borderRadius: 8,
  cursor: 'pointer', border: '0.5px solid #534AB7', background: '#534AB7', color: '#fff', fontWeight: 500 }
