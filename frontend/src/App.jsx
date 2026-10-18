import { useEffect, useMemo, useState } from 'react'
import { API, authFetch } from './auth'
import BeltForecast from './BeltForecast'
import CameraVideo from './CameraVideo'
import { selectActiveAlarm } from './liveAlerts'
import { getTranslation, LANGUAGE_OPTIONS, RTL_LANGUAGES } from './i18n'
import { getDashboardCopy } from './dashboardCopy'
import './dashboard.css'

export function Icon({ name, size = 26, strokeWidth = 1.8 }) {
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
      <div className="sidebar-brand"><Icon name="conveyor" size={38} /><div className="sidebar-brand-copy"><strong>CONVEYOR</strong><span>AI MONITOR</span></div></div>
      <nav>
        {items.map(([icon, label, active]) => (
          <button className={`nav-item ${active ? 'active' : ''}`} key={icon} type="button">
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

function EvidenceViewer({ viewer, onClose, t }) {
  if (!viewer) return null
  const active = viewer.active === 'clip' && viewer.clip_url ? 'clip' : 'snapshot'
  const legacyClip = String(viewer.clip_object || '').toLowerCase().endsWith('.avi')

  return (
    <div className="evidence-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="evidence-modal" role="dialog" aria-modal="true" aria-label={t.evidence} onMouseDown={(event) => event.stopPropagation()}>
        <div className="evidence-modal-header">
          <div>
            <span className={`evidence-severity ${eventTone(viewer.event.severity)}`}>{viewer.event.severity}</span>
            <h3>{eventTitle(viewer.event, t)}</h3>
            <p>{viewer.event.message}</p>
          </div>
          <button className="evidence-close" type="button" onClick={onClose}>{t.close}</button>
        </div>
        <div className="evidence-tabs">
          {viewer.snapshot_url && <button type="button" className={active === 'snapshot' ? 'active' : ''} onClick={() => viewer.setActive('snapshot')}>{t.snapshot}</button>}
          {viewer.clip_url && <button type="button" className={active === 'clip' ? 'active' : ''} onClick={() => viewer.setActive('clip')}>{t.clip}</button>}
        </div>
        <div className="evidence-media">
          {active === 'snapshot' && viewer.snapshot_url && <img src={viewer.snapshot_url} alt={`${eventTitle(viewer.event, t)} ${t.snapshot}`} />}
          {active === 'clip' && viewer.clip_url && !legacyClip && <video key={viewer.clip_url} src={viewer.clip_url} controls autoPlay playsInline />}
          {active === 'clip' && viewer.clip_url && legacyClip && (
            <div className="legacy-clip">
              <p>{t.legacyClip}</p>
              <a href={viewer.clip_url} target="_blank" rel="noreferrer">{t.openClip}</a>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}

export function DamageOverlay({ data, lang, dimensions }) {
  const [now, setNow] = useState(Date.now)
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [])
  const regions = Array.isArray(data?.damage_regions) ? data.damage_regions : []
  const fresh = data?.telemetry_ts && now - Date.parse(data.telemetry_ts) < 10000
  const visible = fresh ? regions : []
  const position = data?.source_position_seconds
  useEffect(() => {
    const video = document.querySelector('.camera-video')
    if (!video) return
    if (visible.length && Number.isFinite(position)) {
      // Show the exact source frame measured by vision while the marker is visible.
      video.pause()
      video.currentTime = position
    } else {
      video.play().catch(() => {})
    }
  }, [data, fresh])
  if (!visible.length) return null
  const frameHeight = dimensions?.width ? 1000 * dimensions.height / dimensions.width : 562.5
  const label = lang === 'fa' ? 'خرابی لبهٔ تسمه' : lang === 'ar' ? 'تلف حافة الحزام' : 'Belt edge damage'
  const critical = data?.tear_status === 'CRITICAL'
  return <svg className={`damage-overlay ${critical ? 'critical' : 'warning'}`} viewBox={`0 0 1000 ${frameHeight}`} preserveAspectRatio="xMidYMid meet" role="img" aria-label={label}>
    <defs><marker id="damage-arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="currentColor" /></marker></defs>
    {visible.map((region, index) => {
      const x = region.x * 1000, y = region.y * frameHeight
      const width = region.width * 1000, height = region.height * frameHeight
      const right = x + width, middle = y + height / 2
      const onLeft = region.x < 0.5
      const end = onLeft ? right + 6 : x - 6
      const start = onLeft ? Math.min(830, right + 150) : Math.max(170, x - 150)
      return <g key={index}>
        <rect x={x} y={y} width={width} height={height} rx="4" className="damage-box" />
        <path d={`M${start},${middle - 36} L${end},${middle}`} className="damage-pointer" markerEnd="url(#damage-arrow)" />
        <rect x={start - 105} y={middle - 73} width="210" height="30" rx="5" className="damage-label-bg" />
        <text x={start} y={middle - 53} textAnchor="middle" className="damage-label">{label}</text>
      </g>
    })}
  </svg>
}

export default function App({ lang, setLang, onLogout, conveyor = {code: "CV-01", video_source: "conveyor_1.mp4"}, conveyors = [], sidebar }) {
  const code = conveyor.code
  const encodedCode = encodeURIComponent(code)
  const t = getTranslation(lang)
  const c = getDashboardCopy(lang)
  const rtl = RTL_LANGUAGES.has(lang)
  const [data, setData] = useState(null)
  const [dimensions, setDimensions] = useState(null)
  const [events, setEvents] = useState([])
  const [alarmEvents, setAlarmEvents] = useState([])
  const [actionError, setActionError] = useState('')
  const [error, setError] = useState('')
  const [acknowledgingId, setAcknowledgingId] = useState(null)
  const [evidenceLoadingId, setEvidenceLoadingId] = useState(null)
  const [evidenceViewer, setEvidenceViewer] = useState(null)
  const [eventFilter, setEventFilter] = useState('all')
  const [expandedEvents, setExpandedEvents] = useState(false)
  const [now, setNow] = useState(Date.now)

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    let mounted = true
    let inFlight = false

    const parseResponse = async (response) => {
      if (response.status === 401) {
        onLogout()
        throw new Error('AUTH')
      }
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return response.json()
    }

    const load = async () => {
      if (inFlight) return
      inFlight = true
      try {
        const [statusResponse, eventsResponse, alarmsResponse] = await Promise.all([
          authFetch(`${API}/conveyors/${encodedCode}/status/`),
          authFetch(`${API}/events/?conveyor=${encodedCode}&limit=100`),
          authFetch(`${API}/events/?conveyor=${encodedCode}&acknowledged=false&active=true&limit=100`),
        ])
        const [statusPayload, eventPayload, alarmsPayload] = await Promise.all([
          statusResponse.status === 503 ? Promise.resolve(null) : parseResponse(statusResponse),
          parseResponse(eventsResponse),
          parseResponse(alarmsResponse),
        ])
        if (!mounted) return
        setData(statusPayload?.telemetry_ts ? statusPayload : null)
        setEvents(Array.isArray(eventPayload) ? eventPayload : [])
        setAlarmEvents(Array.isArray(alarmsPayload) ? alarmsPayload : [])
        setError('')
      } catch (e) {
        if (mounted && e.message !== 'AUTH') setError(e.message)
      } finally { inFlight = false }
    }

    load()
    const timer = window.setInterval(load, 1000)
    return () => {
      mounted = false
      window.clearInterval(timer)
    }
  }, [onLogout, encodedCode])

  async function acknowledgeEvent(eventId) {
    setActionError('')
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
      setAlarmEvents((current) => current.filter((item) => item.id !== updated.id))
    } catch (e) {
      setActionError(e.message)
    } finally {
      setAcknowledgingId(null)
    }
  }

  async function openEvidence(event, preferred = 'snapshot') {
    if (event.evidence_status !== 'READY') {
      setActionError(event.evidence_status === 'PENDING' ? t.evidencePending : t.evidenceUnavailable)
      return
    }
    setEvidenceLoadingId(event.id)
    try {
      const response = await authFetch(`${API}/events/${event.id}/evidence/`)
      if (response.status === 401) {
        onLogout()
        return
      }
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(payload.detail || `HTTP ${response.status}`)
      }
      const payload = await response.json()
      setEvidenceViewer({
        event,
        ...payload,
        active: preferred,
        setActive: (active) => setEvidenceViewer((current) => current ? { ...current, active } : current),
      })
      setActionError('')
    } catch (e) {
      setActionError(e.message)
    } finally {
      setEvidenceLoadingId(null)
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
      alignmentTone: String(data?.alignment_status || "NORMAL").toLowerCase(),
      tearTone: String(data?.tear_status || "NORMAL").toLowerCase(),
      tearRisk,
      confidence,
      plcRunning,
    }
  }, [data, t])

  const activeAlarm = useMemo(
    () => selectActiveAlarm(alarmEvents),
    [alarmEvents],
  )

  const pendingEvents = alarmEvents.filter((event) => event.active && !event.acknowledged)
  const filteredEvents = eventFilter === 'pending' ? pendingEvents : events
  const visibleEvents = expandedEvents ? filteredEvents : filteredEvents.slice(0, 5)
  const sampleTime = Date.parse(data?.telemetry_ts)
  const stale = Boolean(data && (data.state === 'STALE' || !Number.isFinite(sampleTime) || now - sampleTime > 10000))
  const connected = Boolean(data && !error && !stale)
  const systemLabel = error ? c.disconnected : !data ? c.waiting : stale ? c.stale : t.systemOnline
  const conditionLabel = activeAlarm ? c.attention : c.monitoring
  const metricValue = (value) => data ? value : '—'
  const measurementTone = (tone) => connected ? tone : 'unavailable'

  function reviewPendingAlerts() {
    setEventFilter('pending')
    setExpandedEvents(true)
    document.getElementById('dashboard-events')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className={`app-shell operations-ui ${rtl ? 'rtl-ui' : ''}`}>

      {sidebar || <Sidebar t={t} />}
      <main className="dashboard">
        <header className="topbar">
          <div className="title-block">
            <div className="brand-icon"><Icon name="conveyor" size={44} /></div>
            <h1>{t.appName}</h1>
            <span className="title-divider" />
            <select className="conveyor-select" aria-label={lang === "fa" ? "انتخاب تسمه" : "Select conveyor"} value={code} onChange={event => { window.location.hash = `/conveyors/${encodeURIComponent(event.target.value)}` }}>{(conveyors.length ? conveyors : [conveyor]).map(item => <option key={item.code} value={item.code}>{item.code} · {item.name || item.code}</option>)}</select>
          </div>
          <div className="topbar-actions">
            <div className="language-switcher header-language-select">
              <label className="topbar-language-field">
                <span className="topbar-language-label">{t.language}</span>
                <span className="topbar-language-control">
                  <select aria-label={t.language} value={lang} onChange={(event) => setLang(event.target.value)}>
                    {LANGUAGE_OPTIONS.map((item) => (
                      <option key={item.code} value={item.code}>{item.short} — {item.label}</option>
                    ))}
                  </select>
                  <Icon name="chevron" size={15} />
                </span>
              </label>
            </div>
            <div className={`system-state ${connected ? 'is-connected' : 'is-unavailable'}`}>
              <span className="state-dot" />
              <div><strong>{systemLabel}</strong><span>{connected ? conditionLabel : c.monitoring}</span></div>
            </div>
            <button type="button" className="logout-button" onClick={onLogout}>{t.logout}</button>
          </div>
        </header>

        {!conveyor.active && <div className="connection-notice" role="status">{lang === "fa" ? "پایش این تسمه غیرفعال است" : lang === "ar" ? "مراقبة هذا السير معطّلة" : "Monitoring is paused for this conveyor"}</div>}

        {(error || stale) && <div className="connection-notice" role="status"><strong>{systemLabel}</strong><span>{error ? c.retryDetail : c.staleDetail}</span></div>}

        {actionError && <div className="action-notice" role="alert"><span>{[t.evidencePending, t.evidenceUnavailable].includes(actionError) ? actionError : c.actionFailed}</span><button type="button" onClick={() => setActionError('')}>{t.close}</button></div>}

        <section className="summary-grid" aria-label={c.overview}>
          <article className="summary-card">
            <div className="summary-label"><span>{t.beltSpeed}</span><Icon name="speed" size={20} /></div>
            <div className="summary-value"><bdi>{metricValue(view.speed.toFixed(2))}</bdi><small>m/s</small></div>
            <span className="summary-caption">{data ? c.speedDetail : c.noData}</span>
          </article>
          <article className="summary-card">
            <div className="summary-label"><span>{t.materialFlow}</span><Icon name="material" size={20} /></div>
            <div className="summary-value"><bdi>{metricValue(Math.round(view.materialFlow))}</bdi><small>t/h</small></div>
            <span className="summary-caption">{data ? c.flowDetail : c.noData}</span>
          </article>
          <article className={`summary-card ${connected ? view.overloadTone : 'unavailable'}`}>
            <div className="summary-label"><span>{t.overload}</span><Icon name="load" size={20} /></div>
            <div className="summary-value"><bdi>{metricValue(view.loadPercent)}</bdi><small>%</small>{connected && <span className={`metric-badge ${view.overloadBadgeClass}`}>{view.overloadState}</span>}</div>
            <span className="summary-caption">{data ? c.capacity : c.noData}</span>
          </article>
          <article className={`summary-card alert-summary ${activeAlarm ? (activeAlarm.severity === 'CRITICAL' ? 'critical' : 'warning') : ''}`}>
            <div className="summary-label"><span>{c.activeAlerts}</span><Icon name="events" size={20} /></div>
            <div className="summary-value"><bdi>{data ? pendingEvents.length : '—'}</bdi><button className="summary-link" type="button" onClick={reviewPendingAlerts}>{c.reviewAlerts}<Icon name="chevron" size={15} /></button></div>
            <span className="summary-caption">{c.recentWindow}</span>
          </article>
        </section>

        <section className="dashboard-grid">
          <article className="vision-panel" aria-labelledby="vision-title">
            <div className="panel-heading"><div><span className="section-eyebrow"><bdi>{code}</bdi> / VISION</span><h2 id="vision-title">{t.liveVision}</h2></div><span className="source-chip">{c.localVideo}</span></div>
            <div className="camera-scene">
              <CameraVideo conveyor={conveyor} lang={lang} onDimensions={setDimensions} />
              <DamageOverlay data={data} lang={lang} dimensions={dimensions} />
              <div className="live-badge">
                <div><strong>{code}</strong></div>
                <small>{conveyor.camera_name || code}</small>
              </div>
              {activeAlarm && (
                <div role="status" className={`live-alarm-banner ${activeAlarm.severity === 'CRITICAL' ? 'critical' : 'warning'}`}>
                  <div className="live-alarm-copy">
                    <span>{t.liveAlarm}</span>
                    <strong>{eventTitle(activeAlarm, t)}</strong>
                    <small>{activeAlarm.message}</small>
                  </div>
                  <div className="live-alarm-actions">
                    {activeAlarm.evidence_status === 'READY' && activeAlarm.snapshot_object && (
                      <button type="button" disabled={evidenceLoadingId === activeAlarm.id} onClick={() => openEvidence(activeAlarm, 'snapshot')}>{t.snapshot}</button>
                    )}
                    <button type="button" disabled={acknowledgingId === activeAlarm.id} onClick={() => acknowledgeEvent(activeAlarm.id)}>{c.acknowledge}</button>
                  </div>
                </div>
              )}
            </div>
            <div className="camera-footer"><span>{t.offset} <bdi>{metricValue(view.alignment)} mm</bdi></span><span>{c.updated} <bdi>{eventTime(data?.telemetry_ts, lang)}</bdi></span></div>
          </article>

          <article className="telemetry-panel" aria-labelledby="condition-title" data-available={Boolean(data)}>
            <div className="panel-heading"><div><span className="section-eyebrow">{c.metricsDetail}</span><h2 id="condition-title">{c.metrics}</h2></div></div>
            <MetricRow icon="alignment" label={t.alignment} value={metricValue(view.alignment)} unit=" mm" valueClass={`${measurementTone(view.alignmentTone === "normal" ? "good" : view.alignmentTone)}-value`}><Progress value={view.alignment} min={-50} max={50} marker tone={measurementTone(view.alignmentTone)} /></MetricRow>
            <MetricRow icon="shield" label={t.tearRisk} value={metricValue(`${view.tearRisk}%`)} valueClass={`${measurementTone(view.tearTone === "normal" ? "good" : view.tearTone)}-value`}><Progress value={view.tearRisk} min={0} max={100} tone={measurementTone(view.tearTone)} /></MetricRow>
            <MetricRow icon="brain" label={t.aiConfidence} value={metricValue(`${view.confidence}%`)}><Progress value={view.confidence} min={0} max={100} tone={connected ? 'normal' : 'unavailable'} /></MetricRow>
            <div className="metric-row plc-row">
              <div className="metric-icon"><Icon name="plc" size={36}/></div>
              <div className="metric-copy"><span className="metric-label">{t.plcReadOnly}</span><div className={`plc-value ${connected ? '' : 'unavailable-value'}`}>{!connected ? '—' : view.plcRunning ? t.autoRunning : data?.plc_state || c.stopped}</div></div>
              <span className="read-only-chip">{c.readOnly}</span>
            </div>
          </article>
        </section>

        <section className="events-panel" id="dashboard-events" aria-labelledby="events-title">
          <div className="events-header"><div><h2 id="events-title">{t.recentEvents}</h2><span className="events-subtitle">{eventFilter === 'pending' ? c.recentWindow : c.eventDetail.replace('CV-01', code)}</span></div><div className="events-controls"><div className="event-filters" role="group" aria-label={t.events}><button type="button" aria-pressed={eventFilter === 'all'} onClick={() => setEventFilter('all')}>{c.allEvents}</button><button type="button" aria-pressed={eventFilter === 'pending'} onClick={() => setEventFilter('pending')}>{c.pending}<span>{data ? pendingEvents.length : '—'}</span></button></div>{filteredEvents.length > 5 && <button className="events-expand" type="button" onClick={() => setExpandedEvents(!expandedEvents)}>{expandedEvents ? c.showLess : t.viewAll}<Icon name="chevron" size={18}/></button>}</div></div>
          <div className="event-table live-events-table">
            {visibleEvents.length === 0 ? (
              <div className="event-empty">{error ? c.disconnected : !data ? c.waiting : eventFilter === 'pending' ? c.noPending : t.noRecentEvents}</div>
            ) : visibleEvents.map((event) => (
              <div className={`event-row live-event-row ${event.acknowledged && !event.active ? 'is-acknowledged' : ''}`} key={event.id}>
                <time>{eventTime(event.created_at, lang)}</time>
                <span className={`event-dot ${eventTone(event.severity)}`}/>
                <strong className="event-title-with-state">
                  <span>{eventTitle(event, t)}</span>
                  <small className={`event-condition-state ${event.active ? 'active' : 'recovered'}`}>{event.active ? t.activeCondition : t.recovered}</small>
                </strong>
                <span className="event-detail">{event.message}</span>
                <div className="event-actions">
                  {event.evidence_status === 'READY' && event.snapshot_object && (
                    <button className="event-evidence-button" type="button" disabled={evidenceLoadingId === event.id} onClick={() => openEvidence(event, 'snapshot')}>{t.snapshot}</button>
                  )}
                  {event.evidence_status === 'READY' && event.clip_object && (
                    <button className="event-evidence-button" type="button" disabled={evidenceLoadingId === event.id} onClick={() => openEvidence(event, 'clip')}>{t.clip}</button>
                  )}
                  {event.evidence_status === 'PENDING' && <span className="event-evidence-state">{t.evidencePending}</span>}
                  {event.acknowledged ? (
                    <span className="event-acknowledged">{t.acknowledged}</span>
                  ) : (
                    <button className="event-ack-button" type="button" disabled={acknowledgingId === event.id} onClick={() => acknowledgeEvent(event.id)}>{c.acknowledge}</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        <BeltForecast lang={lang} />
      </main>
      <EvidenceViewer viewer={evidenceViewer} onClose={() => setEvidenceViewer(null)} t={t} />
    </div>
  )
}
