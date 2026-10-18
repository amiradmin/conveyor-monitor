import { useCallback, useEffect, useState } from 'react'
import App, { Icon } from './App'
import CameraVideo from './CameraVideo'
import { API, authFetch } from './auth'
import { LANGUAGE_OPTIONS, RTL_LANGUAGES } from './i18n'
import { getFleetCopy } from './fleetCopy'
import './fleet.css'

function useRoute() {
  const read = () => window.location.hash.slice(1) || '/conveyors'
  const [route, setRoute] = useState(read)
  useEffect(() => { const change = () => { setRoute(read()); window.scrollTo({top:0, left:0, behavior:"instant"}) }; window.addEventListener('hashchange', change); return () => window.removeEventListener('hashchange', change) }, [])
  return route
}
function Sidebar({ route, c, conveyors }) {
  return <aside className="sidebar sidebar-enhanced fleet-sidebar"><a className="sidebar-brand" href="#/conveyors"><div className="sidebar-brand-icon"><Icon name="conveyor" /></div><div className="sidebar-brand-copy"><strong>CONVEYOR</strong><span>AI MONITOR</span></div></a><nav className="nav-list" aria-label={c.fleet}>
    <a className={`nav-item ${route === '/conveyors' ? 'active' : ''}`} href="#/conveyors"><Icon name="home" /><span>{c.fleet}</span></a>
    <a className={`nav-item ${route.startsWith('/cameras') ? 'active' : ''}`} href="#/cameras"><Icon name="camera" /><span>{c.cameras}</span></a>
  </nav><div className="fleet-sidebar-belts"><span>{c.monitor}</span>{conveyors.map(item => <a key={item.code} href={`#/conveyors/${encodeURIComponent(item.code)}`} className={route === `/conveyors/${encodeURIComponent(item.code)}` ? 'selected' : ''}><span className={`belt-dot ${item.state === 'RUNNING' ? 'running' : ''}`} /><bdi>{item.code}</bdi><small>{item.pending_alarm_count || ''}</small></a>)}</div></aside>
}
function Header({ title, lang, setLang, onLogout, c }) {
  return <header className="topbar"><div className="title-block"><div className="brand-icon"><Icon name="conveyor" size={38} /></div><h1>{title}</h1></div><div className="topbar-actions"><div className="language-switcher">{LANGUAGE_OPTIONS.map(item => <button type="button" key={item.code} className={lang === item.code ? 'active' : ''} onClick={() => setLang(item.code)}>{item.short}</button>)}</div><button type="button" className="logout-button" onClick={onLogout}>{c.logout}</button></div></header>
}
const stateLabel = (item, c) => ({ RUNNING: c.running, STOPPED: c.stopped, STALE: c.stale, DISABLED: c.disabled, UNAVAILABLE: c.unavailable }[item.state] || c.unavailable)
function Overview({ items, c, lang }) {
  const [query, setQuery] = useState(''), [filter, setFilter] = useState('all')
  const visible = items.filter(item => `${item.code} ${item.name}`.toLowerCase().includes(query.toLowerCase()) && (filter !== 'attention' || item.pending_alarm_count > 0 || ['STALE', 'UNAVAILABLE'].includes(item.state)))
  return <>
    <div className="fleet-page-heading"><div><h2>{c.title}</h2><p>{c.description}</p></div><a className="fleet-primary" href="#/cameras/new">+ {c.add}</a></div>
    <div className="fleet-totals">{[[c.total, items.length], [c.active, items.filter(item => item.active).length], [c.alerts, items.reduce((sum, item) => sum + item.pending_alarm_count, 0)], [c.critical, items.reduce((sum, item) => sum + item.critical_alarm_count, 0)]].map(([label, value]) => <article key={label}><span>{label}</span><strong>{value}</strong></article>)}</div>
    <div className="fleet-toolbar"><input type="search" aria-label={c.search} placeholder={c.search} value={query} onChange={event => setQuery(event.target.value)} /><div className="event-filters"><button type="button" aria-pressed={filter === 'all'} onClick={() => setFilter('all')}>{c.all}</button><button type="button" aria-pressed={filter === 'attention'} onClick={() => setFilter('attention')}>{c.attention}</button></div></div>
    <div className="belt-grid">{visible.map(item => <article key={item.code} className={`belt-card ${item.critical_alarm_count ? 'critical' : ''}`}><a className="belt-preview" href={`#/conveyors/${encodeURIComponent(item.code)}`} aria-label={`${c.open} ${item.code}`}><CameraVideo conveyor={item} preview lang={lang} /><bdi className="preview-id">{item.code}</bdi></a><div className="belt-card-body"><div className="belt-card-heading"><div><h3>{item.name}</h3><span>{item.camera_name}</span></div><span className={`belt-state ${item.state.toLowerCase()}`}>{stateLabel(item, c)}</span></div><div className="belt-metrics"><div><span>m/s</span><strong>{['RUNNING', 'STOPPED'].includes(item.state) ? item.status.speed_mps.toFixed(2) : '—'}</strong></div><div><span>t/h</span><strong>{['RUNNING', 'STOPPED'].includes(item.state) ? Math.round(item.status.material_flow_tph) : '—'}</strong></div><div className={item.pending_alarm_count ? 'needs-attention' : ''}><span>{c.alerts}</span><strong>{item.pending_alarm_count}</strong></div></div><a className="belt-open" href={`#/conveyors/${encodeURIComponent(item.code)}`}>{c.open}<Icon name="chevron" size={18} /></a></div></article>)}</div>
    {!visible.length && <div className="fleet-empty"><Icon name="conveyor" size={48} /><h3>{items.length ? c.noResults : c.empty}</h3>{!items.length && <><p>{c.emptyDetail}</p><a className="fleet-primary" href="#/cameras/new">{c.add}</a></>}</div>}
  </>
}
function ConveyorForm({ item, c, onSave }) {
  const [mode, setMode] = useState(item ? 'existing' : 'sample'), [file, setFile] = useState(null), [error, setError] = useState(''), [saving, setSaving] = useState(false)
  async function submit(event) {
    event.preventDefault(); setError('')
    if (mode === 'upload' && file?.size > 500 * 1024 * 1024) { setError(c.fileHelp); return }
    if (mode === 'upload' && !file) { setError(c.sourceRequired); return }
    const values = new FormData(event.currentTarget)
    if (item) values.delete('code')
    if (mode !== 'sample') values.delete('video_source')
    if (mode === 'upload') values.set('video_file', file)
    setSaving(true)
    try { await onSave(values, item); window.location.hash = '/cameras' } catch (e) { setError(e.message || c.saveError) } finally { setSaving(false) }
  }
  return <form className="conveyor-form" onSubmit={submit}><h2>{item ? c.edit : c.add}</h2><div className="form-fields"><label>{c.name}<input name="name" required maxLength={150} defaultValue={item?.name || ''} /></label><label>{c.code}<input name="code" dir="ltr" required readOnly={!!item} pattern="[A-Z0-9][A-Z0-9_-]{0,49}" maxLength={50} placeholder="CV-02" defaultValue={item?.code || ''} /></label><label>{c.camera}<input name="camera_name" required maxLength={100} defaultValue={item?.camera_name || ''} /></label><label>{c.width}<input name="belt_width_mm" type="number" min={100} max={10000} required defaultValue={item?.belt_width_mm || 1200} /></label></div><fieldset><legend>{c.source}</legend><div className="source-options">{item && <label><input type="radio" checked={mode === 'existing'} onChange={() => setMode('existing')} />{c.existing}</label>}<label><input type="radio" checked={mode === 'sample'} onChange={() => setMode('sample')} />{c.sample}</label><label><input type="radio" checked={mode === 'upload'} onChange={() => setMode('upload')} />{c.upload}</label></div>{mode === 'sample' && <select name="video_source" aria-label={c.sample} defaultValue={item?.video_source || 'conveyor_1.mp4'}><option value="conveyor_1.mp4">conveyor_1.mp4</option><option value="conveyor_1_old.mp4">conveyor_1_old.mp4</option></select>}{mode === 'upload' && <label className="video-upload">{c.file}<input type="file" accept="video/mp4,video/webm,.mp4,.webm" onChange={event => setFile(event.target.files[0] || null)} /></label>}{mode === 'existing' && <p dir="ltr">{item.video_name}</p>}<p className="form-help">{c.fileHelp}</p></fieldset>{error && <div className="action-notice" role="alert">{error}</div>}<div className="form-actions"><button className="fleet-primary" disabled={saving} type="submit">{saving ? c.saving : c.save}</button><a className="fleet-secondary" href="#/cameras">{c.cancel}</a></div></form>
}
function Management({ items, c, toggle, error }) {
  const [busy, setBusy] = useState(null)
  return <><div className="fleet-page-heading"><div><h2>{c.cameras}</h2><p>{c.manageDetail}</p></div><a className="fleet-primary" href="#/cameras/new">+ {c.add}</a></div>{error && <div className="action-notice" role="alert">{error}</div>}<div className="camera-list">{items.map(item => <article key={item.code}><div className="camera-list-icon"><Icon name="camera" /></div><div className="camera-list-name"><h3><bdi>{item.code}</bdi> · {item.name}</h3><p>{item.camera_name} · <bdi>{item.video_name || '—'}</bdi></p></div><span className={`belt-state ${item.state.toLowerCase()}`}>{stateLabel(item, c)}</span><div className="camera-list-actions"><a className="fleet-secondary" href={`#/cameras/${encodeURIComponent(item.code)}`}>{c.configure}</a><button type="button" className="fleet-secondary" disabled={busy === item.code} onClick={async () => { setBusy(item.code); try { await toggle(item) } finally { setBusy(null) } }}>{item.active ? c.disable : c.enable}</button></div></article>)}</div>{!items.length && <div className="fleet-empty"><h3>{c.empty}</h3><p>{c.emptyDetail}</p></div>}</>
}
export default function OperatorApp({ lang, setLang, onLogout }) {
  const route = useRoute(), c = getFleetCopy(lang)
  const [items, setItems] = useState([]), [loaded, setLoaded] = useState(false), [error, setError] = useState(''), [actionError, setActionError] = useState(''), [now, setNow] = useState(Date.now)
  const load = useCallback(async () => {
    const response = await authFetch(`${API}/conveyors/`)
    if (response.status === 401) { onLogout(); return null }
    if (!response.ok) throw new Error(c.loadError)
    const payload = await response.json()
    return payload
  }, [onLogout, c.loadError])
  useEffect(() => {
    let alive = true
    const refresh = async () => { setNow(Date.now()); try { const payload = await load(); if (alive && payload) { setItems(payload); setLoaded(true); setError('') } } catch { if (alive) setError(c.loadError) } }
    refresh(); const timer = setInterval(refresh, 5000)
    return () => { alive = false; clearInterval(timer) }
  }, [load, c.loadError])
  async function save(values, item) {
    const response = await authFetch(`${API}/conveyors/${item ? `${encodeURIComponent(item.code)}/` : ''}`, { method: item ? 'PATCH' : 'POST', body: values })
    if (response.status === 401) { onLogout(); throw new Error(c.saveError) }
    const payload = await response.json()
    if (!response.ok) throw new Error(Object.entries(payload).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(' ') : value}`).join(' · '))
    setItems(current => item ? current.map(value => value.code === item.code ? payload : value) : [...current, payload])
  }
  async function toggle(item) {
    setActionError('')
    try { const values = new FormData(); values.set('active', String(!item.active)); await save(values, item) } catch (e) { setActionError(e.message) }
  }
  const displayItems = items.map(item => item.active && (error || item.status?.telemetry_ts && now - Date.parse(item.status.telemetry_ts) > 10000) ? {...item, state:"STALE"} : item)
  const sidebar = <Sidebar route={route} c={c} conveyors={displayItems} />
  const match = route.match(/^\/(conveyors|cameras)\/([^/]+)$/)
  let code = ''; try { code = match ? decodeURIComponent(match[2]) : '' } catch { /* Invalid URL shows the missing-conveyor page. */ }
  const selected = items.find(item => item.code === code)
  if (match?.[1] === 'conveyors' && selected) return <App key={`${selected.code}:${selected.video_name}:${selected.active}`} lang={lang} setLang={setLang} onLogout={onLogout} conveyor={selected} conveyors={items} sidebar={sidebar} />
  return <div className={`app-shell operations-ui ${RTL_LANGUAGES.has(lang) ? 'rtl-ui' : ''}`}>{sidebar}<main className="dashboard fleet-dashboard"><Header title={route.startsWith('/cameras') ? c.cameras : c.fleet} lang={lang} setLang={setLang} onLogout={onLogout} c={c} />{error && <div className="connection-notice" role="alert">{error}</div>}{!loaded ? <div className="fleet-empty" role="status">{error || c.processing}</div> : route === '/conveyors' ? <Overview items={displayItems} c={c} lang={lang} /> : route === '/cameras' ? <Management items={displayItems} c={c} toggle={toggle} error={actionError} /> : route === '/cameras/new' || match?.[1] === 'cameras' && selected ? <ConveyorForm key={code} item={selected} c={c} onSave={save} /> : <div className="fleet-empty"><h2>{c.unknown}</h2><a href="#/conveyors">{c.back}</a></div>}</main></div>
}
