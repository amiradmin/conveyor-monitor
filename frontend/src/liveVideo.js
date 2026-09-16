const VIDEO_SELECTOR = '.camera-video'
const SCENE_SELECTOR = '.camera-scene'

function attachVideo() {
  const scene = document.querySelector(SCENE_SELECTOR)
  if (!scene || scene.querySelector(VIDEO_SELECTOR)) return

  const video = document.createElement('video')
  video.className = 'camera-video'
  video.src = '/conveyor_1.mp4'
  video.autoplay = true
  video.loop = true
  video.muted = true
  video.playsInline = true
  video.preload = 'auto'
  video.setAttribute('aria-label', 'Conveyor live vision demo')

  video.addEventListener('error', () => {
    // Keep the existing generated conveyor scene as a visual fallback
    // when the local demo asset has not been copied into frontend/public yet.
    video.remove()
  }, { once: true })

  scene.prepend(video)

  const resolution = scene.querySelector('.live-badge small')
  if (resolution) resolution.innerHTML = 'CV-01&nbsp;&nbsp;·&nbsp;&nbsp;1280 × 720'

  video.play().catch(() => {
    // Muted autoplay is normally permitted; if a browser blocks it,
    // the video will start as soon as playback becomes allowed.
  })
}

export function mountLiveVideo() {
  attachVideo()

  const observer = new MutationObserver(() => attachVideo())
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  })

  return () => {
    observer.disconnect()
    document.querySelectorAll(VIDEO_SELECTOR).forEach((video) => video.remove())
  }
}
