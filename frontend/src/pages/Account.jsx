import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi, userApi } from '../api'
import { useAuth } from '../auth/AuthContext'
import { Card, COLORS } from '../components/ui'
import { Field, PasswordStrength, SubmitButton, Alert } from '../auth/authUi'

export default function Account() {
  const { user, setUser, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  return (
    <div style={{ maxWidth: 620, margin: '2rem auto', padding: '0 1rem' }}>
      <h2 style={{ fontSize: 20, fontWeight: 500, marginBottom: 4 }}>Account settings</h2>
      <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 20 }}>
        Manage your profile, password, and sessions.
      </p>

      <ProfileSection user={user} setUser={setUser} />
      <ChangePasswordSection />
      <SessionsSection />
      <DangerZone onDeleted={() => { logout(); navigate('/signup') }} />
    </div>
  )
}

function ProfileSection({ user, setUser }) {
  const [name, setName] = useState(user.full_name)
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)

  const save = async (ev) => {
    ev.preventDefault()
    setMsg(null); setLoading(true)
    try {
      const res = await userApi.updateProfile({ full_name: name })
      setUser(res.user)
      setMsg({ kind: 'success', text: 'Profile updated.' })
    } catch (err) {
      setMsg({ kind: 'error', text: err.message || 'Could not update profile.' })
    } finally { setLoading(false) }
  }

  return (
    <Card title="Profile" accent={COLORS.purple}>
      {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
      <form onSubmit={save}>
        <Field label="Full name" name="full_name" value={name} onChange={setName} autoComplete="name" />
        <div style={{ marginBottom: 14 }}>
          <label style={{ display: 'block', fontSize: 12.5, fontWeight: 500, marginBottom: 5 }}>Email</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 14 }}>{user.email}</span>
            <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 6,
              background: user.email_verified ? '#E1F5EE' : '#FAEEDA',
              color: user.email_verified ? '#0F6E56' : '#BA7517' }}>
              {user.email_verified ? 'Verified' : 'Unverified'}
            </span>
          </div>
          <p style={{ fontSize: 11, color: 'var(--color-text-secondary)', margin: '6px 0 0' }}>
            Email changes aren't supported here for security reasons.
          </p>
        </div>
        {user.created_at && (
          <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', margin: '0 0 14px' }}>
            Member since {new Date(user.created_at).toLocaleDateString()}
          </p>
        )}
        <div style={{ maxWidth: 180 }}>
          <SubmitButton loading={loading}>Save changes</SubmitButton>
        </div>
      </form>
    </Card>
  )
}

function ChangePasswordSection() {
  const [cur, setCur] = useState('')
  const [pw, setPw] = useState('')
  const [confirm, setConfirm] = useState('')
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)

  const save = async (ev) => {
    ev.preventDefault()
    setMsg(null)
    if (pw.length < 12) { setMsg({ kind: 'error', text: 'New password must be at least 12 characters.' }); return }
    if (pw !== confirm) { setMsg({ kind: 'error', text: 'Passwords do not match.' }); return }
    setLoading(true)
    try {
      await authApi.changePassword({ current_password: cur, new_password: pw, confirm_password: confirm })
      setMsg({ kind: 'success', text: 'Password changed. Other sessions were signed out.' })
      setCur(''); setPw(''); setConfirm('')
    } catch (err) {
      setMsg({ kind: 'error', text: err.message || 'Could not change password.' })
    } finally { setLoading(false) }
  }

  return (
    <Card title="Change password" accent={COLORS.blue}>
      {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
      <form onSubmit={save}>
        <Field label="Current password" name="current_password" type="password" value={cur}
          onChange={setCur} autoComplete="current-password" />
        <Field label="New password" name="new_password" type="password" value={pw}
          onChange={setPw} autoComplete="new-password" />
        <PasswordStrength password={pw} />
        <Field label="Confirm new password" name="confirm_new" type="password" value={confirm}
          onChange={setConfirm} autoComplete="new-password" />
        <div style={{ maxWidth: 200 }}>
          <SubmitButton loading={loading}>Update password</SubmitButton>
        </div>
      </form>
    </Card>
  )
}

function SessionsSection() {
  const [sessions, setSessions] = useState([])
  const [msg, setMsg] = useState(null)
  const { logout } = useAuth()
  const navigate = useNavigate()

  const load = () => userApi.listSessions().then(r => setSessions(r.sessions || [])).catch(() => {})
  useEffect(() => { load() }, [])

  const signOutAll = async () => {
    setMsg(null)
    try {
      await authApi.logoutAll()
      await logout()
      navigate('/login')
    } catch (err) {
      setMsg({ kind: 'error', text: err.message || 'Could not sign out all sessions.' })
    }
  }

  return (
    <Card title="Active sessions" accent={COLORS.green}>
      {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
      {sessions.length === 0 && <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>No active sessions found.</p>}
      {sessions.map(s => (
        <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '8px 0', borderBottom: '0.5px solid var(--color-border-tertiary)' }}>
          <div>
            <p style={{ margin: 0, fontSize: 13 }}>
              {s.current ? 'This device' : 'Other session'}
              {s.current && <span style={{ fontSize: 11, color: '#1D9E75', marginLeft: 6 }}>· current</span>}
            </p>
            <p style={{ margin: 0, fontSize: 11, color: 'var(--color-text-secondary)' }}>
              Signed in {s.created_at ? new Date(s.created_at).toLocaleString() : ''}
            </p>
          </div>
        </div>
      ))}
      <button onClick={signOutAll} style={{ ...secondaryBtn, marginTop: 12 }}>Sign out of all devices</button>
    </Card>
  )
}

function DangerZone({ onDeleted }) {
  const [confirming, setConfirming] = useState(false)
  const [password, setPassword] = useState('')
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)

  const del = async (ev) => {
    ev.preventDefault()
    setMsg(null); setLoading(true)
    try {
      await userApi.deleteAccount(password)
      onDeleted()
    } catch (err) {
      setMsg({ kind: 'error', text: err.message || 'Could not delete account.' })
    } finally { setLoading(false) }
  }

  return (
    <Card title="Delete account" accent={COLORS.red}>
      <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.6, marginTop: 0 }}>
        Deleting your account removes your profile and sign-in data permanently. Your past
        interview results are anonymised (unlinked from your identity), not kept against your name.
        This cannot be undone.
      </p>
      {!confirming ? (
        <button onClick={() => setConfirming(true)} style={dangerBtn}>Delete my account</button>
      ) : (
        <form onSubmit={del}>
          {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
          <Field label="Confirm your password to delete" name="del_password" type="password"
            value={password} onChange={setPassword} autoComplete="current-password" />
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" onClick={() => setConfirming(false)} style={secondaryBtn}>Cancel</button>
            <button type="submit" disabled={loading} style={{ ...dangerBtn, flex: 1, opacity: loading ? 0.6 : 1 }}>
              {loading ? 'Deleting…' : 'Permanently delete'}
            </button>
          </div>
        </form>
      )}
    </Card>
  )
}

const secondaryBtn = { fontSize: 13, padding: '9px 16px', borderRadius: 8, cursor: 'pointer',
  border: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-primary)',
  color: 'var(--color-text-primary)' }
const dangerBtn = { fontSize: 13, padding: '9px 16px', borderRadius: 8, cursor: 'pointer',
  border: '0.5px solid #D94848', background: '#FCEBEB', color: '#791F1F', fontWeight: 500 }
