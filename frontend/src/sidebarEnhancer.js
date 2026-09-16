const SIDEBAR_SELECTOR = '.sidebar'

function scrollToElement(selector) {
  const element = document.querySelector(selector)
  if (!element) return
  element.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function activeAlarmCount() {
  return [...document.querySelectorAll('.live-event-row')].filter((row) => {
    const active = row.querySelector('.event-condition-state.active')
    const needsAck = row.querySelector('.event-ack-button')
    return Boolean(active && needsAck)
  }).length
}

function updateEventBadge(sidebar) {
  const eventsButton = sidebar.querySelectorAll('.nav-item')[2]
  if (!eventsButton) return

  let badge = eventsButton.querySelector('.sidebar-alert-badge')
  const count = activeAlarmCount()

  if (count <= 0) {
    badge?.remove()
    return
  }

  if (!badge) {
    badge = document.createElement('span')
    badge.className = 'sidebar-alert-badge'
    badge.setAttribute('aria-label', 'Active alarms')
    eventsButton.appendChild(badge)
  }
  badge.textContent = count > 9 ? '9+' : String(count)
}

function buildSettingsDrawer(sidebar) {
  document.querySelector('.sidebar-settings-drawer')?.remove()

  const buttons = sidebar.querySelectorAll('.nav-item')
  const settingsLabel = buttons[3]?.querySelector('span')?.textContent?.trim() || 'Settings'
  const systemLabel = document.querySelector('.system-state strong')?.textContent?.trim() || 'System Online'
  const systemDetail = document.querySelector('.system-state div span')?.textContent?.trim() || ''
  const plcLabel = document.querySelector('.plc-row .metric-label')?.textContent?.trim() || 'PLC'
  const plcValue = document.querySelector('.plc-row .plc-value')?.textContent?.trim() || 'Read Only'

  const drawer = document.createElement('section')
  drawer.className = 'sidebar-settings-drawer'
  drawer.setAttribute('aria-label', settingsLabel)
  drawer.innerHTML = `
    <div class="sidebar-settings-head">
      <div>
        <span>CV-01</span>
        <strong>${settingsLabel}</strong>
      </div>
      <button type="button" class="sidebar-settings-close" aria-label="Close">×</button>
    </div>
    <div class="sidebar-settings-status">
      <i></i>
      <div><strong>${systemLabel}</strong><span>${systemDetail}</span></div>
    </div>
    <div class="sidebar-settings-language">
      <button type="button" data-lang="EN">EN</button>
      <button type="button" data-lang="FA">FA</button>
      <button type="button" data-lang="AR">AR</button>
    </div>
    <div class="sidebar-settings-plc">
      <span>${plcLabel}</span>
      <strong>${plcValue}</strong>
    </div>
  `

  sidebar.appendChild(drawer)

  const close = () => {
    drawer.remove()
    buttons[3]?.classList.remove('active')
  }

  drawer.querySelector('.sidebar-settings-close')?.addEventListener('click', close)
  drawer.querySelectorAll('[data-lang]').forEach((languageButton) => {
    languageButton.addEventListener('click', () => {
      const code = languageButton.dataset.lang
      const topbarButton = [...document.querySelectorAll('.language-switcher button')]
        .find((button) => button.textContent?.trim().toUpperCase() === code)
      topbarButton?.click()
      close()
    })
  })

  return drawer
}

export function mountSidebarEnhancer() {
  const sidebar = document.querySelector(SIDEBAR_SELECTOR)
  if (!sidebar) return () => {}

  sidebar.classList.add('sidebar-enhanced')

  const brand = sidebar.querySelector('.sidebar-brand')
  if (brand && !brand.querySelector('.sidebar-brand-caption')) {
    const caption = document.createElement('span')
    caption.className = 'sidebar-brand-caption'
    caption.textContent = 'AI'
    brand.appendChild(caption)
  }

  const footer = document.createElement('div')
  footer.className = 'sidebar-status'
  footer.innerHTML = '<span class="sidebar-status-dot"></span><strong>CV-01</strong><small>ONLINE</small>'
  sidebar.appendChild(footer)

  const navItems = [...sidebar.querySelectorAll('.nav-item')]
  const cleanup = []
  let settingsOpen = false

  const activate = (index) => {
    navItems.forEach((item, itemIndex) => item.classList.toggle('active', itemIndex === index))
  }

  navItems.forEach((button, index) => {
    button.removeAttribute('disabled')
    button.setAttribute('aria-current', index === 0 ? 'page' : 'false')

    const handler = () => {
      if (index !== 3) {
        document.querySelector('.sidebar-settings-drawer')?.remove()
        settingsOpen = false
      }

      activate(index)
      navItems.forEach((item, itemIndex) => item.setAttribute('aria-current', itemIndex === index ? 'page' : 'false'))

      if (index === 0) window.scrollTo({ top: 0, behavior: 'smooth' })
      if (index === 1) scrollToElement('.vision-panel')
      if (index === 2) scrollToElement('.events-panel')
      if (index === 3) {
        const existing = document.querySelector('.sidebar-settings-drawer')
        if (existing) {
          existing.remove()
          settingsOpen = false
          activate(0)
        } else {
          buildSettingsDrawer(sidebar)
          settingsOpen = true
        }
      }
    }

    button.addEventListener('click', handler)
    cleanup.push(() => button.removeEventListener('click', handler))
  })

  const onScroll = () => {
    if (settingsOpen) return
    const events = document.querySelector('.events-panel')
    const vision = document.querySelector('.vision-panel')
    const eventsTop = events?.getBoundingClientRect().top ?? Number.POSITIVE_INFINITY
    const visionTop = vision?.getBoundingClientRect().top ?? Number.POSITIVE_INFINITY

    if (eventsTop < window.innerHeight * 0.52) activate(2)
    else if (visionTop < 150 && window.scrollY > 60) activate(1)
    else activate(0)
  }

  window.addEventListener('scroll', onScroll, { passive: true })
  cleanup.push(() => window.removeEventListener('scroll', onScroll))

  const mutationObserver = new MutationObserver(() => updateEventBadge(sidebar))
  mutationObserver.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] })
  updateEventBadge(sidebar)

  return () => {
    cleanup.forEach((dispose) => dispose())
    mutationObserver.disconnect()
    document.querySelector('.sidebar-settings-drawer')?.remove()
    footer.remove()
    sidebar.querySelector('.sidebar-brand-caption')?.remove()
    sidebar.classList.remove('sidebar-enhanced')
  }
}
