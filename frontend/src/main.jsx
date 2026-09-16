import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import Login from './Login'
import { clearTokens, hasSession } from './auth'
import { RTL_LANGUAGES } from './i18n'
import { mountLiveVideo } from './liveVideo'
import { mountLiveAlerts } from './liveAlerts'
import { mountSidebarEnhancer } from './sidebarEnhancer'
import './styles.css'
import './auth.css'
import './liveVideo.css'
import './brand.css'
import './events.css'
import './liveAlerts.css'
import './sidebar.css'
import './sidebarDropdown.css'
import './headerLanguage.css'

function Root() {
  const [authenticated, setAuthenticated] = useState(hasSession())
  const [lang, setLangState] = useState(() => localStorage.getItem('conveyor_language') || 'en')

  const setLang = (next) => {
    localStorage.setItem('conveyor_language', next)
    setLangState(next)
  }

  useEffect(() => {
    document.documentElement.lang = lang
    document.documentElement.dir = RTL_LANGUAGES.has(lang) ? 'rtl' : 'ltr'
  }, [lang])

  useEffect(() => {
    if (!authenticated) return undefined
    const unmountVideo = mountLiveVideo()
    const unmountAlerts = mountLiveAlerts()
    const unmountSidebar = mountSidebarEnhancer()
    return () => {
      unmountSidebar?.()
      unmountAlerts?.()
      unmountVideo?.()
    }
  }, [authenticated])

  const logout = () => {
    clearTokens()
    setAuthenticated(false)
  }

  return authenticated
    ? <App lang={lang} setLang={setLang} onLogout={logout} />
    : <Login lang={lang} setLang={setLang} onAuthenticated={() => setAuthenticated(true)} />
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><Root /></React.StrictMode>,
)
