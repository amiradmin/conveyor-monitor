import { useState } from 'react'
import { login } from './auth'
import { getTranslation, LANGUAGE_OPTIONS, RTL_LANGUAGES } from './i18n'

function ConveyorMark() {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <path d="M7 46h50M16 41l5-24h23l5 24M25 17V9h14v8M39 9h6v18M45 15h9"/>
      <rect x="46" y="12" width="9" height="6" rx="1.5"/>
      <circle cx="17" cy="48" r="5"/><circle cx="47" cy="48" r="5"/>
      <path d="M13 33h39M23 26h19"/>
    </svg>
  )
}

export default function Login({ lang, setLang, onAuthenticated }) {
  const t = getTranslation(lang)
  const rtl = RTL_LANGUAGES.has(lang)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(username.trim(), password)
      onAuthenticated()
    } catch (err) {
      setError(err.message === 'invalid_credentials' ? t.invalidCredentials : t.loginUnavailable)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-shell" dir={rtl ? 'rtl' : 'ltr'}>
      <div className="login-grid-bg" />
      <section className="login-brand-panel">
        <div className="login-brand-lockup">
          <div className="login-mark"><ConveyorMark /></div>
          <div><span>{t.monitoring}</span><h1>{t.appName}</h1></div>
        </div>
        <div className="login-visual">
          <div className="login-belt"><i/><i/><i/><i/><i/></div>
          <div className="scan-line" />
          <div className="vision-frame"><span>CV-01</span><b>AI VISION</b></div>
        </div>
        <div className="security-note"><span className="state-dot small"/><span>{t.secureJwt}</span></div>
      </section>

      <section className="login-form-panel">
        <div className="login-language">
          {LANGUAGE_OPTIONS.map((item) => (
            <button key={item.code} className={lang === item.code ? 'active' : ''} onClick={() => setLang(item.code)} type="button">{item.short}</button>
          ))}
        </div>
        <form className="login-card" onSubmit={submit}>
          <div className="login-card-icon"><ConveyorMark /></div>
          <h2>{t.signInTitle}</h2>
          <p>{t.signInSubtitle}</p>
          <label><span>{t.username}</span><input autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder={t.usernamePlaceholder} required autoFocus /></label>
          <label><span>{t.password}</span><input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t.passwordPlaceholder} required /></label>
          {error && <div className="login-error">{error}</div>}
          <button className="login-submit" type="submit" disabled={loading}>{loading ? t.signingIn : t.signIn}</button>
          <div className="login-jwt"><span className="lock-dot">●</span>{t.secureJwt}</div>
        </form>
      </section>
    </main>
  )
}
