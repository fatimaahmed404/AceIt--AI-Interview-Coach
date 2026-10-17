import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../api'
import { AuthShell, Field, Checkbox, PasswordStrength, SubmitButton, Alert } from '../auth/authUi'

export default function Signup() {
  const [form, setForm] = useState({
    full_name: '', email: '', password: '', confirm_password: '', accept_terms: false,
  })
  const [errors, setErrors] = useState({})
  const [alert, setAlert] = useState(null)
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const set = (k) => (v) => setForm(f => ({ ...f, [k]: v }))

  const clientValidate = () => {
    const e = {}
    if (form.full_name.trim().length < 2) e.full_name = 'Please enter your full name.'
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email)) e.email = 'Enter a valid email.'
    if (form.password.length < 12) e.password = 'At least 12 characters.'
    if (form.password !== form.confirm_password) e.confirm_password = 'Passwords do not match.'
    if (!form.accept_terms) e.accept_terms = 'You must accept the terms.'
    return e
  }

  const submit = async (ev) => {
    ev.preventDefault()
    setAlert(null)
    const e = clientValidate()
    setErrors(e)
    if (Object.keys(e).length) return
    setLoading(true)
    try {
      const res = await authApi.register(form)
      setDone(true)
      if (res.email_delivery === 'failed') {
        setAlert({ kind: 'info', msg: 'Account created, but the verification email could not be sent. Try resending from the login page shortly.' })
      }
    } catch (err) {
      if (err.data?.fields) setErrors(err.data.fields)
      else setAlert({ kind: 'error', msg: err.message || 'Registration failed.' })
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <AuthShell title="Check your email"
        subtitle={`We sent a verification link to ${form.email}. Click it to activate your account.`}
        footer={<>Already verified? <Link to="/login" style={linkStyle}>Log in</Link></>}>
        {alert && <Alert kind={alert.kind}>{alert.msg}</Alert>}
        <Alert kind="success">
          If you don't see the email, check your spam folder or resend verification from the login page.
        </Alert>
        <button onClick={() => navigate('/login')} style={secondaryBtn}>Go to login</button>
      </AuthShell>
    )
  }

  return (
    <AuthShell title="Create your account"
      subtitle="Start practicing interviews with instant AI feedback."
      footer={<>Already have an account? <Link to="/login" style={linkStyle}>Log in</Link></>}>
      {alert && <Alert kind={alert.kind}>{alert.msg}</Alert>}
      <form onSubmit={submit} noValidate>
        <Field label="Full name" name="full_name" value={form.full_name}
          onChange={set('full_name')} error={errors.full_name} autoComplete="name" autoFocus />
        <Field label="Email" name="email" type="email" value={form.email}
          onChange={set('email')} error={errors.email} autoComplete="email" />
        <Field label="Password" name="password" type="password" value={form.password}
          onChange={set('password')} error={errors.password} autoComplete="new-password" />
        <PasswordStrength password={form.password} />
        <Field label="Confirm password" name="confirm_password" type="password"
          value={form.confirm_password} onChange={set('confirm_password')}
          error={errors.confirm_password} autoComplete="new-password" />
        <Checkbox name="accept_terms" checked={form.accept_terms} onChange={set('accept_terms')}
          error={errors.accept_terms}
          label="I accept the Terms of Service and Privacy Policy." />
        <SubmitButton loading={loading}>Create account</SubmitButton>
      </form>
    </AuthShell>
  )
}

const linkStyle = { color: '#534AB7', textDecoration: 'none', fontWeight: 500 }
const secondaryBtn = { width: '100%', fontSize: 14, padding: '10px 16px', borderRadius: 8,
  cursor: 'pointer', border: '0.5px solid var(--color-border-tertiary)',
  background: 'var(--color-background-primary)', color: 'var(--color-text-primary)' }
