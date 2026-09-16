import { API, authFetch, clearTokens } from './auth'

const OVERLAY_ID = 'live-vision-alarm-overlay'
const POLL_MS = 2000

const titles = {
  en: {
    ALIGNMENT_WARNING: 'Alignment warning',
    ALIGNMENT_CRITICAL: 'Critical alignment',
    TEAR_WARNING: 'Tear risk warning',
    TEAR_CRITICAL: 'Critical tear risk',
    OVERLOAD_WARNING: 'Overload warning',
    OVERLOAD_CRITICAL: 'Critical overload',
    acknowledge: 'ACKNOWLEDGE',
  },
  fa: {
    ALIGNMENT_WARNING: 'هشدار هم‌راستایی',
    ALIGNMENT_CRITICAL: 'بحرانی: هم‌راستایی',
    TEAR_WARNING: 'هشدار ریسک پارگی',
    TEAR_CRITICAL: 'بحرانی: ریسک پارگی',
    OVERLOAD_WARNING: 'هشدار اضافه‌بار',
    OVERLOAD_CRITICAL: 'بحرانی: اضافه‌بار',
    acknowledge: 'تأیید هشدار',
  },
  ar: {
    ALIGNMENT_WARNING: 'تحذير المحاذاة',
    ALIGNMENT_CRITICAL: 'محاذاة حرجة',
    TEAR_WARNING: 'تحذير خطر التمزق',
    TEAR_CRITICAL: 'خطر تمزق حرج',
    OVERLOAD_WARNING: 'تحذير الحمل الزائد',
    OVERLOAD_CRITICAL: 'حمل زائد حرج',
    acknowledge: 'تأكيد التنبيه',
  },
}

function currentLanguage() {
  const language = document.documentElement.lang || 'en'
  return titles[language] ? language : 'en'
}

function removeOverlay() {
  document.getElementById(OVERLAY_ID)?.remove()
}

function eventTitle(event) {
  const lang = currentLanguage()
  return titles[lang][event.code] || String(event.code || 'ALARM').replaceAll('_', ' ')
}

async function acknowledge(eventId, button) {
  button.disabled = true
  try {
    const response = await authFetch(`${API}/events/${eventId}/acknowledge/`, { method: 'POST' })
    if (response.status === 401) {
      clearTokens()
      window.location.reload()
      return
    }
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    removeOverlay()
  } catch (error) {
    button.disabled = false
    button.dataset.error = 'true'
  }
}

function renderOverlay(event) {
  const scene = document.querySelector('.camera-scene')
  if (!scene) return

  let overlay = document.getElementById(OVERLAY_ID)
  const tone = event.severity === 'CRITICAL' ? 'critical' : 'warning'
  const lang = currentLanguage()

  if (!overlay) {
    overlay = document.createElement('div')
    overlay.id = OVERLAY_ID
    scene.appendChild(overlay)
  }

  overlay.className = `live-alert-overlay ${tone}`
  overlay.setAttribute('role', 'alert')
  overlay.innerHTML = ''

  const icon = document.createElement('div')
  icon.className = 'live-alert-icon'
  icon.textContent = '!'

  const copy = document.createElement('div')
  copy.className = 'live-alert-copy'
  const severity = document.createElement('span')
  severity.className = 'live-alert-severity'
  severity.textContent = event.severity || 'WARNING'
  const heading = document.createElement('strong')
  heading.textContent = eventTitle(event)
  const message = document.createElement('small')
  message.textContent = event.message || ''
  copy.append(severity, heading, message)

  const button = document.createElement('button')
  button.type = 'button'
  button.className = 'live-alert-ack'
  button.textContent = titles[lang].acknowledge
  button.addEventListener('click', () => acknowledge(event.id, button))

  overlay.append(icon, copy, button)
}

async function fetchLatestAlarm() {
  const response = await authFetch(`${API}/events/?conveyor=CV-01&acknowledged=false&limit=1`)
  if (response.status === 401) {
    clearTokens()
    window.location.reload()
    return null
  }
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  const payload = await response.json()
  return Array.isArray(payload) && payload.length ? payload[0] : null
}

export function mountLiveAlerts() {
  let stopped = false
  let running = false

  const tick = async () => {
    if (stopped || running) return
    running = true
    try {
      const event = await fetchLatestAlarm()
      if (stopped) return
      if (event) renderOverlay(event)
      else removeOverlay()
    } catch {
      // Dashboard connectivity state already reports backend failures.
    } finally {
      running = false
    }
  }

  tick()
  const timer = window.setInterval(tick, POLL_MS)

  return () => {
    stopped = true
    window.clearInterval(timer)
    removeOverlay()
  }
}
