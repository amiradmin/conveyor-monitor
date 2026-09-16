import { useEffect, useMemo, useState } from 'react'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

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
    conveyor: <><path d="M3 17h18"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="18" r="2"/><path d="M5 15h13l2-8H7L5 15Z"/><path d="m9 7 2-4h4l-1 4"/></>,
    speed: <><path d="M4.5 17a8 8 0 1 1 15 0"/><path d="m12 13 4-4"/><path d="M7 10.5 5.5 9M12 8V5.5M17 10.5 18.5 9"/></>,
    alignment: <><path d="M8 7v10M16 7v10"/><path d="M3 12h5M16 12h5"/><path d="m5 10-2 2 2 2M19 10l2 2-2 2"/></>,
    material: <><path d="m4 17 5-8 3 5 3-7 5 10H4Z"/><path d="M7 17h10"/></>,
    shield: <><path d="M12 3 20 6v6c0 5-3.4 8-8 10-4.6-2-8-5-8-10V6l8-3Z"/><path d="M9.5 12h5"/><path d="m12 9.5 1 2.5-1 2.5-1-2.5 1-2.5Z"/></>,
    brain: <><path d="M9.5 4.5A3 3 0 0 0 5 7v.5A3.5 3.5 0 0 0 4 14a3 3 0 0 0 3 5h1"/><path d="M14.5 4.5A3 3 0 0 1 19 7v.5a3.5 3.5 0 0 1 1 6.5 3 3 0 0 1-3 5h-1"/><path d="M9 4v16M15 4v16M9 8H7.5M15 8h1.5M9 12H6.5M15 12h2.5M9 16H7.5M15 16h1.5"/></>,
    plc: <><rect x="7" y="4" width="10" height="16" rx="2"/><path d="M10 1v3M14 1v3M10 20v3M14 20v3M4 8h3M4 12h3M4 16h3M17 8h3M17 12h3M17 16h3"/><rect x="10" y="8" width="4" height="6" rx=".7"/></>,
    chevron: <path d="m9 6 6 6-6 6"/>,
  }

  return <svg {...common}>{icons[name] || icons.home}</svg>
}

function Progress({ value, min = 0, max = 100, marker = false }) {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100))
  return (
    <div className="progress-wrap">
      <div className="progress-track">
        {marker ? <span className="progress-marker" style={{ left: `${pct}%` }} /> : <span className="progress-fill" style={{ width: `${pct}%` }} />}
      </div>
      <div className="progress-scale"><span>{min}</span><span>{marker ? 0 : max}</span>{marker && <span>{max}</span>}</div>
    </div>
  )
}

function MetricRow({ icon, label, value, unit = '', children, valueClass = '' }) {
  return (
    <div className="metric-row">
      <div className="metric-icon"><Icon name={icon} size={36} /></div>
      <div className="metric-copy">
        <span className="metric-label">{label}</span>
        <div className={`metric-value ${valueClass}`}>{value}<small>{unit}</small></div>
      </div>
      <div className="metric-visual">{children}</div>
    </div>
  )
}

function Sidebar() {
  const items = [
    ['home', 'Home', true],
    ['camera', 'Live\nVision', false],
    ['events', 'Events', false],
    ['settings', 'Settings', false],
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-brand"><Icon name="conveyor" size={38} /></div>
      <nav>
        {items.map(([icon, label, active]) => (
          <button className={`nav-item ${active ? 'active' : ''}`} key={label} type="button">
            <Icon name={icon} size={24} />
            <span>{label.split('\n').map((part, i) => <span key={i}>{part}</span>)}</span>
          </button>
        ))}
      </nav>
    </aside>
  )
}

export default function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    const load = () => {
      fetch(`${API}/demo/status/`)
        .then((r) => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
        .then((payload) => {
          if (!mounted) return
          setData(payload)
          setError('')
        })
        .catch((e) => mounted && setError(e.message))
    }
    load()
    const timer = window.setInterval(load, 5000)
    return () => {
      mounted = false
      window.clearInterval(timer)
    }
  }, [])

  const view = useMemo(() => {
    const speed = Number(data?.speed_mps ?? 2.36)
    const alignment = Number(data?.alignment_offset_mm ?? -12)
    const materialFlow = Number(data?.mass_flow_tph ?? data?.material_flow_tph ?? 412)
    const tearRisk = Math.round(Number(data?.tear_probability ?? 0.03) * 100)
    const confidence = Math.round(Number(data?.ai_confidence ?? 0.96) * 100)
    const plcRunning = data?.plc_state ? /run|auto/i.test(data.plc_state) : true
    return { speed, alignment, materialFlow, tearRisk, confidence, plcRunning }
  }, [data])

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="dashboard">
        <header className="topbar">
          <div className="title-block">
            <div className="brand-icon"><Icon name="conveyor" size={44} /></div>
            <h1>Conveyor AI Monitor</h1>
            <span className="title-divider" />
            <span className="asset-id">CV-01</span>
          </div>
          <div className="system-state">
            <span className="state-dot" />
            <div><strong>System Online</strong><span>{error ? 'Telemetry reconnecting' : 'All systems nominal'}</span></div>
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
              <div className="offset-guide"><i/><i/><span>Offset<strong>{view.alignment} mm</strong></span></div>
              <div className="live-badge">
                <div><span className="state-dot small"/> <strong>Live Vision</strong></div>
                <small>CV-01&nbsp;&nbsp;·&nbsp;&nbsp;1920 × 1080</small>
              </div>
            </div>
          </article>

          <article className="telemetry-panel">
            <MetricRow icon="speed" label="Belt Speed" value={view.speed.toFixed(2)} unit=" m/s">
              <Progress value={view.speed} min={0} max={4} />
            </MetricRow>
            <MetricRow icon="alignment" label="Alignment" value={view.alignment} unit=" mm">
              <Progress value={view.alignment} min={-50} max={50} marker />
            </MetricRow>
            <MetricRow icon="material" label="Material Flow" value={Math.round(view.materialFlow)} unit=" t/h">
              <Progress value={view.materialFlow} min={0} max={800} />
            </MetricRow>
            <MetricRow icon="shield" label="Tear Risk" value={`${view.tearRisk}%`} valueClass="good-value">
              <Progress value={view.tearRisk} min={0} max={100} />
            </MetricRow>
            <MetricRow icon="brain" label="AI Confidence" value={`${view.confidence}%`}>
              <Progress value={view.confidence} min={0} max={100} />
            </MetricRow>
            <div className="metric-row plc-row">
              <div className="metric-icon"><Icon name="plc" size={36}/></div>
              <div className="metric-copy"><span className="metric-label">PLC Read Only</span><div className="plc-value">{view.plcRunning ? 'Auto (Running)' : 'Connected'}</div></div>
              <Icon name="chevron" size={25}/>
            </div>
          </article>
        </section>

        <section className="events-panel">
          <div className="events-header"><h2>Recent Events</h2><button type="button">View All <Icon name="chevron" size={18}/></button></div>
          <div className="event-table">
            <div className="event-row"><time>10:24:11</time><span className="event-dot ok"/><strong>System Online</strong><span className="event-detail">CV-01 operating normally</span></div>
            <div className="event-row"><time>10:17:03</time><span className="event-dot ok"/><strong>Alignment within range</strong><span className="event-detail">Offset {view.alignment} mm</span></div>
            <div className="event-row"><time>10:03:45</time><span className="event-dot ok"/><strong>Material flow stable</strong><span className="event-detail">{Math.round(view.materialFlow)} t/h</span></div>
            <div className="event-row"><time>09:41:22</time><span className="event-dot warn"/><strong>Alignment warning (auto-corrected)</strong><span className="event-detail">Offset -28 mm → {view.alignment} mm</span></div>
            <div className="event-row"><time>08:55:18</time><span className="event-dot ok"/><strong>PLC mode confirmed</strong><span className="event-detail">Auto (Running)</span></div>
          </div>
        </section>
      </main>
    </div>
  )
}
