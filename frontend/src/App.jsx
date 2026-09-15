import { useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

function Metric({ label, value, unit = '', status }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}{unit && <small> {unit}</small>}</strong>
      {status && <em className={`status ${status.toLowerCase()}`}>{status}</em>}
    </div>
  )
}

export default function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API}/demo/status/`)
      .then((r) => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
      .then(setData)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <main>
      <header>
        <div>
          <p className="eyebrow">INDUSTRIAL VISION · PLC MONITORING</p>
          <h1>Conveyor AI Monitor</h1>
        </div>
        <div className="online"><i /> SYSTEM ONLINE</div>
      </header>

      <section className="grid">
        <article className="camera-panel">
          <div className="panel-title"><span>CV-01 · TOP CAMERA</span><b>LIVE</b></div>
          <div className="camera-placeholder">
            <div className="belt">
              <div className="center-line" />
              <div className="material" />
            </div>
            <span>RTSP CAMERA FEED</span>
          </div>
        </article>

        <article className="telemetry">
          <div className="panel-title"><span>CV-01 TELEMETRY</span><b>{data?.state || 'LOADING'}</b></div>
          {error && <p className="error">Backend unavailable: {error}</p>}
          <div className="metrics">
            <Metric label="Belt speed" value={data?.speed_mps ?? '—'} unit="m/s" status="NORMAL" />
            <Metric label="Alignment" value={data?.alignment_offset_mm ?? '—'} unit="mm" status={data?.alignment_status || '—'} />
            <Metric label="Material volume" value={data?.volume_m3h ?? '—'} unit="m³/h" status="NORMAL" />
            <Metric label="Tear detection" value={data ? `${Math.round(data.tear_probability * 100)}%` : '—'} status={data?.tear_status || '—'} />
            <Metric label="AI confidence" value={data ? `${Math.round(data.ai_confidence * 100)}%` : '—'} status="GOOD" />
            <Metric label="PLC control" value={data?.plc_write_enabled ? 'ARMED' : 'READ ONLY'} status={data?.plc_write_enabled ? 'WARNING' : 'SAFE'} />
          </div>
        </article>
      </section>

      <section className="bottom-grid">
        <article>
          <div className="panel-title"><span>ALIGNMENT TREND</span><b>LAST 60 SEC</b></div>
          <div className="chart-placeholder"><div className="trend" /></div>
        </article>
        <article>
          <div className="panel-title"><span>RECENT EVENTS</span><b>CV-01</b></div>
          <div className="events">
            <p><time>13:21:04</time><span>Alignment nominal</span><b className="ok-dot">NORMAL</b></p>
            <p><time>13:20:42</time><span>Vision heartbeat</span><b className="ok-dot">GOOD</b></p>
            <p><time>13:20:10</time><span>PLC gateway heartbeat</span><b className="safe-dot">READ ONLY</b></p>
          </div>
        </article>
      </section>
    </main>
  )
}
