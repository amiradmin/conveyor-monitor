import { useEffect, useMemo, useState } from 'react'
import { API, authFetch } from './auth'
import { getTranslation, LANGUAGE_OPTIONS, RTL_LANGUAGES } from './i18n'

function Icon({ name, size = 26, strokeWidth = 1.8 }) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    'aria-hidden': true,
  }

  const icons = {
    home: <><path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10.5V20h13v-9.5"/><path d="M9.5 20v-6h5v6"/></>,
    camera: <><rect x="3" y="6" width="14" height="12" rx="2"/><path d="m17 10 4-2v8l-4-2"/><circle cx="10" cy="12" r="2.6"/></>,
    events: <><path d="M8 6h13M8 12h13M8 18h13"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06-2.83 2.83-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21h-4v-.1A1.7 1.7 0 0 0 8.6 19.4a1.7 1.7 0 0 0-1.87.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3v-4h.1A1.7 1.7 0 0 0 4.6 8.6a1.7 1.7 0 0 0-.34-1.87l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3h4v.1A1.7 1.7 0 0 0 15.4 4.6a1.7 1.7 0 0 0 1.87-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 9c.2.4.6.8 1 1 .35.18.73.29 1.1.3h.1v4h-.1c-.38.01-.75.12-1.1.3-.4.2-.8.6-1 1Z"/></>,
    conveyor: <><path d="M2.5 17.5h18.8"/><path d="M6 15.2 7.6 7h8.8l1.6 8.2"/><path d="M9.3 7V4.4h5.4V7"/><path d="M14.8 4.4h2.2v6.1"/><path d="M17 6.2h3.1"/><rect x="17.2" y="5.2" width="3.2" height="2.1" rx=".5"/><circle cx="6.3" cy="18.2" r="1.7"/><circle cx="17.9" cy="18.2" r="1.7"/><path d="M4.9 12.2h14.4"/><path d="M8.3 9.9h7.4"/></>,
    speed: <><path d="M4.5 17a8 8 0 1 1 15 0"/><path d="m12 13 4-4"/><path d="M7 10.5 5.5 9M12 8V5.5M17 10.5 18.5 9"/></>,
    alignment: <><path d="M8 7v10M16 7v10"/><path d="M3 12h5M16 12h5"/><path d="m5 10-2 2 2 2M19 10l2 2-2 2"/></>,
    material: <><path d="m4 17 5-8 3 5 3-7 5 10H4Z"/><path d="M7 17h10"/></>,
    load: <><path d="M4 18h16"/><path d="M7 18V9.5h10V18"/><path d="M9 9.5 12 5l3 4.5"/><path d="M9.5 13h5"/><path d="M9.5 15.7h5"/></>,
    shield: <><path d="M12 3 20 6v6c0 5-3.4 8-8 10-4.6-2-8-5-8-10V6l8-3Z"/><path d="M9.5 12h5"/><path d="m12 9.5 1 2.5-1 2.5-1-2.5 1-2.5Z"/></>,
    brain: <><path d="M9.5 4.5A3 3 0 0 0 5 7v.5A3.5 3.5 0 0 0 4 14a3 3 0 0 0 3 5h1"/><path d="M14.5 4.5A3 3 0 0 1 19 7v.5a3.5 3.5 0 0 1 1 6.5 3 3 0 0 1-3 5h-1"/><path d="M9 4v16M15 4v16M9 8H7.5M15 8h1.5M9 12H6.5M15 12h2.5M9 16H7.5M15 16h1.5"/></>,
    plc: <><rect x="7" y="4" width="10" height="16" rx="2"/><path d="M10 1v3M14 1v3M10 20v3M14 20v3M4 8h3M4 12h3M4 16h3M17 8h3M17 12h3M17 16h3"/><rect x="10" y="8" width="4" height="6" rx=".7"/></>,
    chevron: <path d="m9 6 6 6-6 6"/>,
  }

  return <svg {...common}>{icons[name] || icons.home}</svg>
}

function Progress({ value, min = 0, max = 100, marker = false, tone = 'normal' }) {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100))
  return (
    <div className="progress-wrap">
      <div className={`progress-track ${tone}`}>
        {marker ? <span className="progress-marker" style={{ left: `${pct}%` }} /> : <span className="progress-fill" style={{ width: `${pct}%` }} />}
      </div>
      <div className="progress-scale"><span>{min}</span><span>{marker ? 0 : max}</span>{marker && <span>{max}</span>}</div>
    </div>
  )
}

function MetricRow({ icon, label, value, unit = '', children, valueClass = '', badge = '', badgeClass = '' }) {
  return (
    <div className="metric-row">
      <div className="metric-icon"><Icon name={icon} size={36} /></div>
      <div className="metric-copy">
        <span className="metric-label">{label}</span>
        <div className={`metric-value ${valueClass}`}>{value}<small>{unit}</small></div>
        {badge && <span className={`metric-badge ${badgeClass}`}>{badge}</span>}
      </div>
      <div className="metric-visual">{children}</div>
    </div>
  )
}

function Sidebar({ t }) {
  const items = [
    ['home', t.home, true],
    ['camera', t.liveVision, false],
    ['events', t.events, false],
    ['settings', t.settings, false],
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-brand"><Icon name="conveyor" size={38} /></div>
      <nav>
        {items.map(([icon, label, active]) => (
          <button className={`nav-item ${active ? 'active' : ''}`} key={label} type="button">
            <Icon name={icon} size={24} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </aside>
  )
}

function eventTone(severity) {
  if (severity === 'CRITICAL') return 'alarm'
  if (severity === 'WARNING') return 'warn'
  return 'ok'
}

function eventTitle(event, t) {
  const map = {
    ALIGNMENT_WARNING: t.alarmAlignmentWarning,
    ALIGNMENT_CRITICAL: t.alarmAlignmentCritical,
    TEAR_WARNING: t.alarmTearWarning,
    TEAR_CRITICAL: t.alarmTearCritical,
    OVERLOAD_WARNING: t.alarmOverloadWarning,
    OVERLOAD_CRITICAL: t.alarmOverloadCritical,
  }
  return map[event.code] || String(event.code || 'EVENT').replaceAll('_', ' ')
}

function eventTime(value, lang) {
  if (!value) return '--:--:--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--:--:--'
  const locale = lang === 'fa' ? 'fa-IR' : lang === 'ar' ? 'ar' : 'en-GB'
  return new Intl.DateTimeFormat(locale, { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(date)
}

export default function App({ lang, setLang, onLogout }) {
  const t = getTranslation(lang)
  const rtl = RTL_LANGUAGES.has(lang)
  const [data, setData] = useState(null)
  const [events, setEvents] = useState([])
  const [error, setError] = useState('')
  const [acknowledgingId, setAcknowledgingId] = useState(null)

  useEffect(() => {
    let mounted = true

    const parseResponse = async (response) => {
      if (response.status === 401) {
        onLogout()
        throw new Error('AUTH')
      }
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return response.json()
    }

    const load = async () => {
      try {
        const [statusResponse, eventsResponse] = await Promise.all([
          authFetch(`${API}/conveyors/CV-01/status/`),
          authFetch(`${API}/events/?conveyor=CV-01&limit=5`),
        ])
        const [statusPayload, eventPayload] = await Promise.all([
          parseResponse(statusResponse),
          parseResponse(eventsResponse),
        ])
        if (!mounted) return
        setData(statusPayload)
        setEvents(Array.isArray(eventPayload) ? eventPayload : [])
        setError('')
      } catch (e) {
        if (mounted && e.message !== 'AUTH') setError(e.message)
      }
    }

    load()
    const timer = window.setInterval(load, 5000)
    return () => {
      mounted = false
      window.clearInterval(timer)
    }
  }, [onLogout])

  async function acknowledgeEvent(eventId) {
    setAcknowledgingId(eventId)
    try {
      const response = await authFetch(`${API}/events/${eventId}/acknowledge/`, { method: 'POST' })
      if (response.status === 401) {
        onLogout()
        return
      }
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const updated = await response.json()
      setEvents((current) => current.map((item) => item.id === updated.id ? updated : item))
    } catch (e) {
      setError(e.message)
    } finally {
      setAcknowledgingId(null)
    }
  }

  const view = useMemo(() => {
    const speed = Number(data?.speed_mps ?? 0)
    const alignment = Number(data?.alignment_offset_mm ?? 0)
    const materialFlow = Number(data?.mass_flow_tph ?? data?.material_flow_tph ?? 0)
    const capacity = Number(data?.nominal_capacity_tph ?? data?.design_capacity_tph ?? 600)
    const loadPercent = Math.max(0, Math.round(Number(data?.load_percent ?? (capacity > 0 ? (materialFlow / capacity) * 100 : 0))))
    const tearRisk = Math.round(Number(data?.tear_probability ?? 0) * 100)
    const confidence = Math.round(Number(data?.ai_confidence ?? 0) * 100)
    const plcRunning = data?.plc_state ? /run|auto/i.test(data.plc_state) : false

    let overloadState = t.normal
    let overloadTone = 'normal'
    let overloadValueClass = 'good-value'

    if (loadPercent >= 100) {
      overloadState = t.overloadState
      overloadTone = 'critical'
      overloadValueClass = 'critical-value'
    } else if (loadPercent >= 80) {
      overloadState = t.high
      overloadTone = 'warning'
      overloadValueClass = 'warning-value'
    }

    return {
      speed,
      alignment,
      materialFlow,
      capacity,
      loadPercent,
      overloadState,
      overloadBadgeClass: overloadTone === 'critical' ? 'overload' : overloadTone === 'warning' ? 'high' : 'normal',
      overloadTone,
      overloadValueClass,
      tearRisk,
      confidence,
      plcRunning,
    }
  }, [data, t])

  return (
    <div className={`app-shell ${rtl ? 'rtl-ui' : ''}`}>
      <Sidebar t={t} />
      <main className="dashboard">
        <header className="topbar">
          <div className="title-block">
            <div className="brand-icon"><Icon name="conveyor" size={44} /></div>
            <h1>{t.appName}</h1>
            <span className="title-divider" />
            <span className="asset-id">CV-01</span>
          </div>
          <div className="topbar-actions">
            <div className="language-switcher">
              {LANGUAGE_OPTIONS.map((item) => <button type="button" key={item.code} className={lang === item.code ? 'active' : ''} onClick={() => setLang(item.code)}>{item.short}</button>)}
            </div>
            <div className="system-state">
              <span className="state-dot" />
              <div><strong>{t.systemOnline}</strong><span>{error ? t.reconnecting : t.allNominal}</span></div>
            </div>
            <button type="button" className="logout-button" onClick={onLogout}>{t.logout}</button>
          </div>
        </header>

        <section className="dashboard-grid">
          <article className="vision-panel">
            <div className="camera-scene">
              <div className="scene-rails scene-rails-left" />
              <div className="scene-rails scene-rails-right" />
              <div className="scene-belt">
                <div className="ore ore-1"/><div className="ore ore-2"/><div className="ore ore-3"/><div className="ore ore-4"/><div className="ore ore-5"/><div className="ore ore-6"/><div className="ore ore-7"/><div className="ore ore-8"/><div className="ore ore-9"/><div className="ore ore-10"/><div className="ore ore-11"/><div className="ore ore-12"/><div className="ore ore-13"/><div className="ore ore-14"/><div className="ore ore-15"/>
              </div>
              <div className="lane-line left"/><div className="lane-line right"/><div className="center-guide" />
              <div className="offset-guide"><i/><i/><span>{t.offset}<strong>{view.alignment} mm</strong></span></div>
              <div className="live-badge">
                <div><span className="state-dot small"/> <strong>{t.liveVision}</strong></div>
                <small>CV-01&nbsp;&nbsp;·&nbsp;&nbsp;1280 × 720</small>
              </div>
            </div>
          </article>

          <article className="telemetry-panel">
            <MetricRow icon="speed" label={t.beltSpeed} value={view.speed.toFixed(2)} unit=" m/s"><Progress value={view.speed} min={0} max={4} /></MetricRow>
            <MetricRow icon="alignment" label={t.alignment} value={view.alignment} unit=" mm"><Progress value={view.alignment} min={-50} max={50} marker /></MetricRow>
            <MetricRow icon="material" label={t.materialFlow} value={Math.round(view.materialFlow)} unit=" t/h"><Progress value={view.materialFlow} min={0} max={800} /></MetricRow>
            <MetricRow icon="load" label={t.overload} value={`${view.loadPercent}%`} valueClass={view.overloadValueClass} badge={view.overloadState} badgeClass={view.overloadBadgeClass}><Progress value={Math.min(view.loadPercent, 120)} min={0} max={120} tone={view.overloadTone} /></MetricRow>
            <MetricRow icon="shield" label={t.tearRisk} value={`${view.tearRisk}%`} valueClass="good-value"><Progress value={view.tearRisk} min={0} max={100} /></MetricRow>
            <MetricRow icon="brain" label={t.aiConfidence} value={`${view.confidence}%`}><Progress value={view.confidence} min={0} max={100} /></MetricRow>
            <div className="metric-row plc-row">
              <div className="metric-icon"><Icon name="plc" size={36}/></div>
              <div className="metric-copy"><span className="metric-label">{t.plcReadOnly}</span><div className="plc-value">{view.plcRunning ? t.autoRunning : t.connected}</div></div>
              <Icon name="chevron" size={25}/>
            </div>
          </article>
        </section>

        <section className="events-panel">
          <div className="events-header"><h2>{t.recentEvents}</h2><button type="button">{t.viewAll} <Icon name="chevron" size={18}/></button></div>
          <div className="event-table live-events-table">
            {events.length === 0 ? (
              <div className="event-empty"><span className="event-dot ok"/>{t.noRecentEvents}</div>
            ) : events.map((event) => (
              <div className={`event-row live-event-row ${event.acknowledged ? 'is-acknowledged' : ''}`} key={event.id}>
                <time>{eventTime(event.created_at, lang)}</time>
                <span className={`event-dot ${eventTone(event.severity)}`}/>
                <strong>{eventTitle(event, t)}</strong>
                <span className="event-detail">{event.message}</span>
                {event.acknowledged ? (
                  <span className="event-acknowledged">{t.acknowledged}</span>
                ) : (
                  <button className="event-ack-button" type="button" disabled={acknowledgingId === event.id} onClick={() => acknowledgeEvent(event.id)}>{t.acknowledge}</button>
                )}
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
