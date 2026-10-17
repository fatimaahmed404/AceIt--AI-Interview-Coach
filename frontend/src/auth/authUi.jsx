import { useState } from 'react'

const ACCENT = '#534AB7'

/** Centered card layout for all auth pages. */
export function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div style={{
      minHeight: 'calc(100vh - 52px)', display: 'flex', alignItems: 'flex-start',
      justifyContent: 'center', padding: '3rem 1rem',
    }}>
      <div style={{ width: '100%', maxWidth: 400 }}>
        <div style={{
          background: 'var(--color-background-secondary)', borderRadius: 14,
          border: '0.5px solid var(--color-border-tertiary)', padding: '28px 26px',
        }}>
          <h1 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 4px' }}>{title}</h1>
          {subtitle && (
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', margin: '0 0 20px', lineHeight: 1.5 }}>
              {subtitle}
            </p>
          )}
          {children}
        </div>
        {footer && (
          <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 16 }}>
            {footer}
          </p>
        )}
      </div>
    </div>
  )
}

/** Labelled text/password input with accessible markup + optional error. */
export function Field({ label, type = 'text', value, onChange, error, autoComplete,
                       placeholder, name, inputMode, maxLength, autoFocus }) {
  const [show, setShow] = useState(false)
  const isPassword = type === 'password'
  const effectiveType = isPassword && show ? 'text' : type
  return (
    <div style={{ marginBottom: 14 }}>
      <label htmlFor={name} style={labelStyle}>{label}</label>
      <div style={{ position: 'relative' }}>
        <input
          id={name}
          name={name}
          type={effectiveType}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          placeholder={placeholder}
          inputMode={inputMode}
          maxLength={maxLength}
          autoFocus={autoFocus}
          aria-invalid={!!error}
          aria-describedby={error ? `${name}-err` : undefined}
          style={{ ...inputStyle, borderColor: error ? '#D94848' : 'var(--color-border-tertiary)',
                   paddingRight: isPassword ? 64 : 12 }}
        />
        {isPassword && (
          <button type="button" onClick={() => setShow(s => !s)}
            aria-label={show ? 'Hide password' : 'Show password'}
            style={toggleStyle}>
            {show ? 'Hide' : 'Show'}
          </button>
        )}
      </div>
      {error && <p id={`${name}-err`} role="alert" style={errStyle}>{error}</p>}
    </div>
  )
}

/** Checkbox with inline label (for terms acceptance). */
export function Checkbox({ label, checked, onChange, name, error }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 12.5,
                      color: 'var(--color-text-secondary)', cursor: 'pointer' }}>
        <input type="checkbox" name={name} checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          style={{ marginTop: 2, accentColor: ACCENT }} />
        <span>{label}</span>
      </label>
      {error && <p role="alert" style={errStyle}>{error}</p>}
    </div>
  )
}

/** Password strength meter + guidance. */
export function PasswordStrength({ password }) {
  const { score, label, color } = scorePassword(password)
  if (!password) return null
  return (
    <div style={{ margin: '-6px 0 14px' }}>
      <div style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
        {[0, 1, 2, 3].map(i => (
          <div key={i} style={{
            flex: 1, height: 4, borderRadius: 2,
            background: i < score ? color : 'var(--color-background-primary)',
          }} />
        ))}
      </div>
      <p style={{ margin: 0, fontSize: 11, color: 'var(--color-text-secondary)' }}>
        Strength: <span style={{ color }}>{label}</span> · at least 12 characters with a mix of
        upper/lowercase, numbers, and symbols.
      </p>
    </div>
  )
}

export function scorePassword(pw) {
  if (!pw) return { score: 0, label: '', color: '#999' }
  let s = 0
  if (pw.length >= 12) s++
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) s++
  if (/\d/.test(pw)) s++
  if (/[^A-Za-z0-9]/.test(pw)) s++
  const map = [
    { label: 'Very weak', color: '#D94848' },
    { label: 'Weak', color: '#EF9F27' },
    { label: 'Fair', color: '#EF9F27' },
    { label: 'Good', color: '#378ADD' },
    { label: 'Strong', color: '#1D9E75' },
  ]
  return { score: s, ...map[s] }
}

/** Primary submit button with loading state. */
export function SubmitButton({ children, loading, disabled }) {
  return (
    <button type="submit" disabled={loading || disabled} style={{
      width: '100%', fontSize: 14, padding: '11px 16px', borderRadius: 8,
      cursor: loading || disabled ? 'not-allowed' : 'pointer',
      border: '0.5px solid #534AB7', background: '#534AB7', color: '#fff', fontWeight: 500,
      opacity: loading || disabled ? 0.6 : 1, display: 'flex', alignItems: 'center',
      justifyContent: 'center', gap: 8,
    }}>
      {loading && <span style={{
        width: 14, height: 14, border: '2px solid #fff', borderTopColor: 'transparent',
        borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite',
      }} />}
      {children}
      <style>{`@keyframes spin {to {transform: rotate(360deg)}}`}</style>
    </button>
  )
}

/** Inline alert banner (error / success / info). */
export function Alert({ kind = 'error', children }) {
  if (!children) return null
  const palette = {
    error: { bg: '#FCEBEB', border: '#F09595', color: '#791F1F' },
    success: { bg: '#E1F5EE', border: '#8FD9C3', color: '#0F6E56' },
    info: { bg: '#E6F1FB', border: '#A9CFF0', color: '#0C447C' },
  }[kind]
  return (
    <div role={kind === 'error' ? 'alert' : 'status'} style={{
      background: palette.bg, border: `0.5px solid ${palette.border}`, color: palette.color,
      borderRadius: 10, padding: '10px 14px', fontSize: 13, marginBottom: 16, lineHeight: 1.5,
    }}>{children}</div>
  )
}

const labelStyle = { display: 'block', fontSize: 12.5, fontWeight: 500, marginBottom: 5,
                     color: 'var(--color-text-primary)' }
const inputStyle = { width: '100%', boxSizing: 'border-box', fontSize: 14, padding: '9px 12px',
                     borderRadius: 8, border: '0.5px solid', background: 'var(--color-background-primary)',
                     color: 'var(--color-text-primary)', outline: 'none' }
const toggleStyle = { position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                      background: 'none', border: 'none', color: '#534AB7', fontSize: 12,
                      cursor: 'pointer', padding: 4 }
const errStyle = { margin: '5px 0 0', fontSize: 12, color: '#D94848' }
