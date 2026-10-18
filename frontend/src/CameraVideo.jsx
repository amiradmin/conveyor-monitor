import { useEffect, useState } from 'react'
import { API, authFetch } from './auth'

export default function CameraVideo({ conveyor, preview = false, lang = 'en', onDimensions }) {
  const [source, setSource] = useState('')
  const [failed, setFailed] = useState(false)
  const [loaded, setLoaded] = useState(false)
  useEffect(() => {
    let alive = true
    let objectUrl
    setSource(''); setFailed(false); setLoaded(false)
    if (preview && conveyor?.video_endpoint) return () => { alive = false }
    if (conveyor?.video_endpoint) {
      authFetch(`${API}${conveyor.video_endpoint}`).then(async response => {
        if (!response.ok) throw new Error('Video unavailable')
        const blob = await response.blob()
        if (!alive) return
        objectUrl = URL.createObjectURL(blob)
        setSource(objectUrl)
      }).catch(() => { if (alive) setFailed(true) })
    } else if (conveyor?.video_source) {
      setSource(`/${encodeURIComponent(conveyor.video_source)}`)
    } else setFailed(true)
    return () => { alive = false; if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [conveyor?.video_endpoint, conveyor?.video_source, conveyor?.video_name, preview])
  const fa = lang === 'fa', ar = lang === 'ar'
  if (preview && conveyor?.video_endpoint) return <div className="video-status uploaded-preview"><span>▶</span><bdi>{conveyor.video_name}</bdi></div>
  return <>
    {(!loaded || failed) && <div className="video-status" role="status">{failed ? (fa ? 'فایل ویدیو در دسترس نیست' : ar ? 'الفيديو غير متاح' : 'Video unavailable') : (fa ? 'در حال بارگذاری ویدیو…' : ar ? 'جارٍ تحميل الفيديو…' : 'Loading video…')}</div>}
    {source && !failed && <video className="camera-video" src={source} autoPlay={!preview} loop muted playsInline controls={!preview} preload={preview ? 'metadata' : 'auto'} aria-label={`${conveyor.code} — ${conveyor.camera_name}`} onLoadedMetadata={event => onDimensions?.({width: event.currentTarget.videoWidth, height: event.currentTarget.videoHeight})} onLoadedData={() => setLoaded(true)} onError={() => setFailed(true)} />}
  </>
}
