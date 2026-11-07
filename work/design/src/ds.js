const ICONS = {
  air: '<path d="M12 2.75c.83 0 1.4.95 1.4 2.1v4.4l7.1 4.15v1.85l-7.1-2.05v4.3l2.1 1.6v1.4L12 19.6l-3.5.9v-1.4l2.1-1.6v-4.3L3.5 15.25V13.4l7.1-4.15v-4.4c0-1.15.57-2.1 1.4-2.1Z"/>',
  river: '<path d="M3.5 14.5h17l-2.3 4H5.8Z"/><path d="M7.5 14.5V10h7l2.5 4.5"/><path d="M10.5 10V6.5"/><path d="M2.5 21.5c1.6 0 1.6-.9 3.2-.9s1.6.9 3.2.9 1.6-.9 3.2-.9 1.6.9 3.2.9 1.6-.9 3.2-.9 1.6.9 3.1.9"/>',
  winter: '<path d="M5 21.5 9.5 10"/><path d="M19 21.5 14.5 10"/><path d="M12 13.5v1.5"/><path d="M12 18v2.5"/><path d="M12 2.5v5.5"/><path d="M9.6 3.9l4.8 2.7"/><path d="M14.4 3.9l-4.8 2.7"/>',
  ferry: '<path d="M2.5 6.5h6"/><path d="M15.5 17.5h6"/><path d="M8.5 6.5 15.5 17.5" stroke-dasharray="2.2 2.6"/><circle class="fill" cx="8.5" cy="6.5" r="1.8"/><circle class="fill" cx="15.5" cy="17.5" r="1.8"/>',
  road: '<path d="M8.5 3 5 21"/><path d="M15.5 3 19 21"/><path d="M12 4.5v2"/><path d="M12 10v3"/><path d="M12 16.5v3.5"/>',
  settlement: '<path d="M3 20.5h18"/><path d="M5 20.5v-8l5-4 5 4v8"/><path d="M15 20.5v-6.5h4.5v6.5"/><path d="M8.5 20.5V16h3v4.5"/>',
  center: '<circle cx="12" cy="12" r="7.5"/><circle class="fill" cx="12" cy="12" r="2.6"/>',
  capital: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle class="fill" cx="12" cy="12" r="1.6"/>',
  hospital: '<rect x="4" y="4" width="16" height="16" rx="4"/><path d="M12 8.5v7"/><path d="M8.5 12h7"/>',
  summer: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2"/><path d="M12 19.5v2"/><path d="M2.5 12h2"/><path d="M19.5 12h2"/><path d="m5.3 5.3 1.4 1.4"/><path d="m17.3 17.3 1.4 1.4"/><path d="m5.3 18.7 1.4-1.4"/><path d="m17.3 6.7 1.4-1.4"/>',
  snow: '<path d="M12 2.5v19"/><path d="m3.8 7.25 16.4 9.5"/><path d="m3.8 16.75 16.4-9.5"/><path d="M9.5 4 12 5.6 14.5 4"/><path d="M9.5 20 12 18.4 14.5 20"/>',
  calendar: '<rect x="3.5" y="5" width="17" height="15.5" rx="3"/><path d="M3.5 10h17"/><path d="M8 3v4"/><path d="M16 3v4"/><circle class="fill" cx="8" cy="14.5" r="1.1"/><circle class="fill" cx="12" cy="14.5" r="1.1"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  wait: '<path d="M7 3.5h10"/><path d="M7 20.5h10"/><path d="M8 3.5c0 4 4 5 4 8.5s-4 4.5-4 8.5"/><path d="M16 3.5c0 4-4 5-4 8.5s4 4.5 4 8.5"/>',
  people: '<circle cx="9" cy="8" r="3"/><path d="M3.5 19.5c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5"/><circle cx="16.5" cy="9" r="2.5"/><path d="M15.6 14.6c2.4-.3 4.4 1.3 4.9 4.9"/>',
  index: '<path d="M3.5 20.5h17"/><path d="M7 20.5V14"/><path d="M12 20.5V9"/><path d="M17 20.5v-8.5"/><path d="M7 11l5-5 5 3"/><circle class="fill" cx="7" cy="11" r="1.6"/><circle class="fill" cx="12" cy="6" r="1.6"/><circle class="fill" cx="17" cy="9" r="1.6"/>',
  network: '<circle cx="6" cy="6" r="2.4"/><circle cx="18" cy="8" r="2.4"/><circle cx="9" cy="18" r="2.4"/><path d="m8.4 6.3 7.2 1.2"/><path d="m6.6 8.4 1.8 7.2"/><path d="m16.4 9.9-5.8 6.3"/>',
  unlink: '<path d="m10 7.5 1.6-1.6a3.5 3.5 0 0 1 5 5L15 12.5"/><path d="m14 16.5-1.6 1.6a3.5 3.5 0 0 1-5-5L9 11.5"/><path d="m4.5 4.5 2 2"/><path d="m17.5 17.5 2 2"/>',
  scenario: '<path d="M6 4v16"/><path d="M6 8.5c0 3.3 2.2 5 5.5 5H14c2.5 0 4 1.5 4 4V20"/><circle class="fill" cx="6" cy="4" r="1.8"/><circle class="fill" cx="6" cy="20" r="1.8"/><circle class="fill" cx="18" cy="20" r="1.8"/>',
  compare: '<path d="M7.5 4 3.5 8l4 4"/><path d="M3.5 8h13"/><path d="m16.5 12 4 4-4 4"/><path d="M20.5 16h-13"/>',
  layers: '<path d="M12 3.5 21 8.5l-9 5-9-5Z"/><path d="m3 12.5 9 5 9-5"/><path d="m3 16.5 9 5 9-5"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>',
  filter: '<path d="M4 7h9"/><path d="M17 7h3"/><circle cx="15" cy="7" r="2"/><path d="M4 17h3"/><path d="M11 17h9"/><circle cx="9" cy="17" r="2"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5"/><circle class="fill" cx="12" cy="7.75" r="1.15"/>',
  warning: '<path d="M10.3 4.2a2 2 0 0 1 3.4 0l7.6 13.2a2 2 0 0 1-1.7 3H4.4a2 2 0 0 1-1.7-3Z"/><path d="M12 9.5v4"/><circle class="fill" cx="12" cy="16.8" r="1.15"/>',
  error: '<path d="M8.2 3h7.6L21 8.2v7.6L15.8 21H8.2L3 15.8V8.2Z"/><path d="M12 7.5V13"/><circle class="fill" cx="12" cy="16.3" r="1.15"/>',
  success: '<circle cx="12" cy="12" r="9"/><path d="m8 12.3 2.7 2.7L16 9.6"/>',
  check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
  close: '<path d="m6 6 12 12"/><path d="M18 6 6 18"/>',
  "arrow-right": '<path d="M4.5 12h15"/><path d="m13.5 6 6 6-6 6"/>',
  "chevron-right": '<path d="m9.5 6 6 6-6 6"/>',
  "chevron-down": '<path d="m6 9.5 6 6 6-6"/>',
  external: '<path d="M14 4.5h5.5V10"/><path d="M19.5 4.5 11 13"/><path d="M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"/>',
  source: '<path d="M14 3.5H7A1.5 1.5 0 0 0 5.5 5v14A1.5 1.5 0 0 0 7 20.5h10a1.5 1.5 0 0 0 1.5-1.5V8Z"/><path d="M14 3.5V8h4.5"/><path d="M9 13h6"/><path d="M9 16.5h4"/>',
  download: '<path d="M12 4v11"/><path d="m7 10.5 5 5 5-5"/><path d="M4.5 20h15"/>',
  pin: '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.3"/>',
  route: '<path d="M6.8 17.4C9.5 16 8.2 13 12 12s3.4-4.2 5.3-5.5"/><circle cx="5" cy="19" r="2.2"/><circle cx="19" cy="5" r="2.2"/>',
  plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
  minus: '<path d="M5 12h14"/>',
  locate: '<circle cx="12" cy="12" r="7"/><path d="M12 2.5v3"/><path d="M12 18.5v3"/><path d="M2.5 12h3"/><path d="M18.5 12h3"/><circle class="fill" cx="12" cy="12" r="1.8"/>',
  bridge: '<path d="M2.5 15.5h19"/><path d="M4 15.5c2-4 5-6 8-6s6 2 8 6"/><path d="M8 11.4v4.1"/><path d="M12 9.5v6"/><path d="M16 11.4v4.1"/><path d="M4 19.5h16"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.6a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1.1.9-1.1 1.7v.4"/><circle class="fill" cx="12" cy="16.9" r="1.15"/>',
  retry: '<path d="M20 12a8 8 0 1 1-2.6-5.9"/><path d="M20.5 4v4.5H16"/>',
  weight: '<path d="M5 20.5 7 10.5h10l2 10Z"/><circle cx="12" cy="6.5" r="2.4"/>',
  menu: '<path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/>',
  drop: '<path d="M12 3.5s6 6.2 6 10.5a6 6 0 0 1-12 0c0-4.3 6-10.5 6-10.5Z"/>',
  type: '<path d="M5 7V5h14v2"/><path d="M12 5v14"/><path d="M9 19h6"/>',
  grid: '<rect x="3.5" y="3.5" width="17" height="17" rx="3"/><path d="M3.5 9h17"/><path d="M9.5 9v11.5"/>',
  motion: '<path d="M3 12h4l2-5 4 10 2-5h6"/>',
  text: '<path d="M4 6h16"/><path d="M4 11h16"/><path d="M4 16h10"/>',
  share: '<circle cx="18" cy="5.5" r="2.3"/><circle cx="6" cy="12" r="2.3"/><circle cx="18" cy="18.5" r="2.3"/><path d="m8 10.9 8-4.3"/><path d="m8 13.1 8 4.3"/>',
  control: '<rect x="3" y="7.5" width="18" height="9" rx="4.5"/><circle class="fill" cx="16.5" cy="12" r="2.6"/>',
  feedback: '<path d="M4.5 5.5h15v10h-8L7 19v-3.5H4.5Z"/>',
  table: '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><path d="M3.5 9.5h17"/><path d="M3.5 14.5h17"/><path d="M10 9.5v10"/>',
  shapes: '<rect x="3.5" y="3.5" width="8" height="8" rx="2"/><circle cx="16.5" cy="16.5" r="4"/><path d="M16.5 3.5 21 11h-9Z"/>',
  book: '<path d="M4.5 5.5a2 2 0 0 1 2-2h12v15h-12a2 2 0 0 0-2 2Z"/><path d="M4.5 20.5a2 2 0 0 1 2-2h12v2"/>'
}

const MODES = {
  air: { icon: "air", color: "var(--mode-air)", name: "Авиация" },
  river: { icon: "river", color: "var(--mode-river)", name: "Речная линия" },
  winter_road: { icon: "winter", color: "var(--mode-winter)", name: "Зимник" },
  ferry: { icon: "ferry", color: "var(--mode-ferry)", name: "Паром" },
  ice_crossing: { icon: "snow", color: "var(--mode-winter)", name: "Ледовая переправа" },
  pontoon_bridge: { icon: "bridge", color: "var(--mode-ferry)", name: "Понтонный мост" }
}

const root = document.documentElement
const fmt = new Intl.NumberFormat("ru-RU")
const css = (name) => getComputedStyle(root).getPropertyValue(name).trim()
const ms = (name) => Number.parseFloat(css(name)) || 0

function svgIcon(name, cls = "") {
  return `<svg class="ico ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] ?? ""}</svg>`
}

function paintIcons(scope = document) {
  for (const el of scope.querySelectorAll("svg[data-i]")) {
    el.setAttribute("viewBox", "0 0 24 24")
    el.setAttribute("aria-hidden", "true")
    if (!el.classList.contains("ico")) el.classList.add("ico")
    el.innerHTML = ICONS[el.dataset.i] ?? ""
  }
}

function iconGallery() {
  const grid = document.getElementById("icon-grid")
  const names = Object.keys(ICONS)
  grid.innerHTML = names
    .map((name) => `<div class="icon-cell">${svgIcon(name, "s24")}<span>${name}</span></div>`)
    .join("")
  document.getElementById("icon-count").textContent = String(names.length)
}

function replay(el, cls) {
  el.classList.remove(cls)
  void el.offsetWidth
  el.classList.add(cls)
}

function closeWithExit(el, after) {
  el.dataset.state = "closing"
  const done = () => {
    el.removeEventListener("animationend", done)
    after()
  }
  el.addEventListener("animationend", done)
  if (ms("--dur-exit") <= 1) done()
}

function placeSeg(seg) {
  const ind = seg.querySelector(".seg-ind")
  const active = seg.querySelector('[aria-checked="true"]')
  if (!ind || !active) return
  ind.style.width = `${active.offsetWidth}px`
  ind.style.transform = `translateX(${active.offsetLeft}px)`
}

function initSegs() {
  for (const seg of document.querySelectorAll(".seg")) {
    seg.insertAdjacentHTML("afterbegin", '<span class="seg-ind" aria-hidden="true"></span>')
    const buttons = [...seg.querySelectorAll("button")]
    for (const button of buttons) {
      button.setAttribute("role", "radio")
      button.addEventListener("click", () => {
        for (const other of buttons) other.setAttribute("aria-checked", String(other === button))
        placeSeg(seg)
        seg.dispatchEvent(new CustomEvent("change", { detail: button.dataset.value }))
      })
      button.addEventListener("keydown", (event) => {
        const index = buttons.indexOf(button)
        const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0
        if (step === 0) return
        event.preventDefault()
        const next = buttons[(index + step + buttons.length) % buttons.length]
        next.focus()
        next.click()
      })
    }
    const ind = seg.querySelector(".seg-ind")
    const transition = ind.style.transition
    ind.style.transition = "none"
    placeSeg(seg)
    requestAnimationFrame(() => {
      ind.style.transition = transition
    })
  }
  addEventListener("resize", () => document.querySelectorAll(".seg").forEach(placeSeg))
}

function placeTabs(tabs) {
  const ind = tabs.querySelector(".tabs-ind")
  const active = tabs.querySelector('[aria-selected="true"]')
  ind.style.transform = `translateX(${active.offsetLeft}px) scaleX(${active.offsetWidth / 10})`
}

function initTabs() {
  for (const tabs of document.querySelectorAll(".tabs")) {
    tabs.insertAdjacentHTML("beforeend", '<span class="tabs-ind" aria-hidden="true"></span>')
    const list = [...tabs.querySelectorAll(".tab")]
    const panels = document.querySelectorAll(`[data-tabpanel="${tabs.id}"]`)
    for (const tab of list) {
      tab.addEventListener("click", () => {
        for (const other of list) other.setAttribute("aria-selected", String(other === tab))
        placeTabs(tabs)
        panels.forEach((panel) => {
          const show = panel.dataset.tab === tab.dataset.tab
          panel.hidden = !show
          if (show) replay(panel, "swap-in")
        })
      })
    }
    requestAnimationFrame(() => placeTabs(tabs))
  }
  addEventListener("resize", () => document.querySelectorAll(".tabs").forEach(placeTabs))
}

function initToggles() {
  document.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-toggle]")
    if (toggle) {
      const kind = toggle.dataset.toggle
      if (kind === "radio") {
        const group = toggle.closest("[role=radiogroup]")
        group.querySelectorAll("[data-toggle=radio]").forEach((item) => item.setAttribute("aria-checked", String(item === toggle)))
      } else {
        toggle.setAttribute("aria-checked", String(toggle.getAttribute("aria-checked") !== "true"))
      }
    }
    const chip = event.target.closest(".chip[aria-pressed]")
    if (chip) chip.setAttribute("aria-pressed", String(chip.getAttribute("aria-pressed") !== "true"))
  })
  document.addEventListener("keydown", (event) => {
    const toggle = event.target.closest?.("[data-toggle]")
    if (toggle && (event.key === " " || event.key === "Enter")) {
      event.preventDefault()
      toggle.click()
    }
  })
}

let tipWarmUntil = 0
function initTooltips() {
  for (const wrap of document.querySelectorAll(".tip-wrap")) {
    const tip = wrap.querySelector(".tooltip")
    let timer = 0
    const show = () => {
      clearTimeout(timer)
      const instant = performance.now() < tipWarmUntil
      timer = setTimeout(() => {
        tip.hidden = false
        if (instant) tip.dataset.instant = ""
        else delete tip.dataset.instant
        tip.dataset.state = "open"
      }, instant ? 0 : 350)
    }
    const hide = () => {
      clearTimeout(timer)
      if (tip.hidden) return
      tipWarmUntil = performance.now() + 500
      closeWithExit(tip, () => {
        tip.hidden = true
      })
    }
    wrap.addEventListener("pointerenter", show)
    wrap.addEventListener("pointerleave", hide)
    wrap.addEventListener("focusin", show)
    wrap.addEventListener("focusout", hide)
    wrap.addEventListener("keydown", (event) => event.key === "Escape" && hide())
  }
}

function initPopover() {
  const button = document.getElementById("pop-btn")
  const pop = document.getElementById("pop")
  const items = () => [...pop.querySelectorAll(".menu-item")]
  const close = (focusBack = true) => {
    if (pop.hidden || pop.dataset.state === "closing") return
    button.setAttribute("aria-expanded", "false")
    closeWithExit(pop, () => {
      pop.hidden = true
    })
    if (focusBack) button.focus()
  }
  const open = () => {
    pop.hidden = false
    pop.dataset.state = "open"
    button.setAttribute("aria-expanded", "true")
    const selected = pop.querySelector('[aria-selected="true"]') ?? items()[0]
    selected.focus()
  }
  button.addEventListener("click", () => (pop.hidden ? open() : close()))
  pop.addEventListener("keydown", (event) => {
    const list = items()
    const index = list.indexOf(document.activeElement)
    if (event.key === "ArrowDown") list[(index + 1) % list.length].focus()
    else if (event.key === "ArrowUp") list[(index - 1 + list.length) % list.length].focus()
    else if (event.key === "Home") list[0].focus()
    else if (event.key === "End") list[list.length - 1].focus()
    else if (event.key === "Escape") close()
    else return
    event.preventDefault()
  })
  for (const item of items()) {
    item.addEventListener("click", () => {
      items().forEach((other) => other.setAttribute("aria-selected", String(other === item)))
      button.querySelector(".btn-label").textContent = item.querySelector("span").textContent
      close()
    })
  }
  document.addEventListener("pointerdown", (event) => {
    if (!pop.hidden && !pop.contains(event.target) && !button.contains(event.target)) close(false)
  })
}

function initDialog() {
  const overlay = document.getElementById("dialog")
  let opener = null
  const close = () => {
    if (overlay.hidden) return
    closeWithExit(overlay, () => {
      overlay.hidden = true
      opener?.focus()
    })
  }
  document.querySelectorAll("[data-open-dialog]").forEach((button) =>
    button.addEventListener("click", () => {
      opener = button
      overlay.hidden = false
      overlay.dataset.state = "open"
      overlay.querySelector("h3").focus()
    }),
  )
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay || event.target.closest("[data-close]")) close()
  })
  overlay.addEventListener("keydown", (event) => event.key === "Escape" && close())
}

function toast(kind, title, text) {
  const host = document.getElementById("toasts")
  const el = document.createElement("div")
  el.className = "toast"
  el.setAttribute("role", kind === "error" ? "alert" : "status")
  el.innerHTML = `${svgIcon(kind === "error" ? "error" : "success", kind === "error" ? "bad" : "ok")}<div><b>${title}</b><p>${text}</p></div><button class="iconbtn" aria-label="Закрыть уведомление">${svgIcon("close", "s16")}</button>`
  host.append(el)
  let left = kind === "error" ? 10000 : 5000
  let started = performance.now()
  let timer = setTimeout(dismiss, left)
  function dismiss() {
    clearTimeout(timer)
    closeWithExit(el, () => el.remove())
  }
  el.addEventListener("pointerenter", () => {
    clearTimeout(timer)
    left -= performance.now() - started
  })
  el.addEventListener("pointerleave", () => {
    started = performance.now()
    timer = setTimeout(dismiss, left)
  })
  el.querySelector("button").addEventListener("click", dismiss)
}

function initToasts() {
  document.getElementById("toast-ok").addEventListener("click", () => toast("ok", "Сценарий сохранён", "Его можно открыть из списка сценариев региона."))
  document.getElementById("toast-err").addEventListener("click", () => toast("error", "Не удалось пересчитать индекс", "Сервер не ответил за 30 секунд. Попробуйте ещё раз."))
}

function pending(button, duration, after) {
  if (button.getAttribute("aria-busy") === "true") return
  const width = button.offsetWidth
  button.style.minWidth = `${width}px`
  button.setAttribute("aria-busy", "true")
  const spinTimer = setTimeout(() => button.insertAdjacentHTML("beforeend", '<span class="spinner" aria-hidden="true"></span>'), 400)
  setTimeout(() => {
    clearTimeout(spinTimer)
    button.querySelector(".spinner")?.remove()
    button.removeAttribute("aria-busy")
    button.style.minWidth = ""
    after?.()
  }, duration)
}

function initPending() {
  document.querySelectorAll("[data-pending]").forEach((button) =>
    button.addEventListener("click", () => pending(button, 1600, () => toast("ok", "Готово", "Действие выполнено."))),
  )
}

function initDisclosure() {
  for (const box of document.querySelectorAll(".disclosure")) {
    const button = box.querySelector(".disclosure-btn")
    const body = box.querySelector(".disclosure-body")
    button.addEventListener("click", () => {
      const open = box.dataset.open !== "true"
      if (open) {
        body.hidden = false
        requestAnimationFrame(() => {
          box.dataset.open = "true"
        })
      } else {
        box.dataset.open = "false"
        setTimeout(() => {
          if (box.dataset.open === "false") body.hidden = true
        }, ms("--dur-panel"))
      }
      button.setAttribute("aria-expanded", String(open))
    })
  }
}

function countUp(el, from, to, digits = 1) {
  const duration = ms("--dur-slow") * 2
  const start = performance.now()
  const format = new Intl.NumberFormat("ru-RU", { minimumFractionDigits: digits, maximumFractionDigits: digits })
  const tick = (now) => {
    const t = Math.min(1, (now - start) / Math.max(duration, 1))
    const eased = 1 - (1 - t) ** 3
    el.textContent = format.format(from + (to - from) * eased)
    if (t < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

function initScenario() {
  const button = document.getElementById("scn-run")
  const seg = document.getElementById("scn-seg")
  const data = {
    base: { a: 41.2, b: 0.41, d: 0, label: "Базовый вариант" },
    winter: { a: 27.6, b: 0.28, d: -13.6, label: "Зимник не открылся" },
    air: { a: 46.9, b: 0.47, d: 5.7, label: "Рейс два раза в неделю" }
  }
  let current = "base"
  let chosen = "base"
  seg.addEventListener("change", (event) => {
    chosen = event.detail
  })
  button.addEventListener("click", () => {
    const panel = document.getElementById("scn-panel")
    panel.classList.add("stale")
    pending(button, 1100, () => {
      panel.classList.remove("stale")
      const from = data[current]
      const to = data[chosen]
      countUp(document.getElementById("scn-value"), from.a, to.a)
      document.getElementById("scn-bar").style.setProperty("--v", String(to.b))
      const delta = document.getElementById("scn-delta")
      delta.className = `stat-delta ${to.d >= 0 ? "up" : "down"}`
      delta.innerHTML = to.d === 0 ? "без изменений" : `${svgIcon(to.d > 0 ? "plus" : "minus", "s16")}${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 }).format(Math.abs(to.d))} к базовому`
      swapText(document.getElementById("scn-label"), to.label)
      current = chosen
    })
  })
}

function swapText(box, text) {
  const old = box.firstElementChild
  const next = document.createElement("span")
  next.textContent = text
  next.className = "swap-in"
  if (old) {
    old.className = "swap-out"
    setTimeout(() => old.remove(), ms("--dur-fast-exit") + 20)
  }
  box.append(next)
}

function drawCurves() {
  for (const svg of document.querySelectorAll("svg.curve")) {
    const [x1, y1, x2, y2] = css(svg.dataset.ease).replace(/cubic-bezier\(|\)/g, "").split(",").map(Number)
    const w = 200
    const h = 100
    const p = (x, y) => `${(x * w).toFixed(1)},${(h - y * h).toFixed(1)}`
    svg.setAttribute("viewBox", "-6 -6 212 112")
    svg.innerHTML = `<path class="axis" d="M0 ${h}H${w}M0 ${h}V0"/><path class="c" d="M${p(0, 0)}C${p(x1, y1)} ${p(x2, y2)} ${p(1, 1)}"/>`
  }
}

function runCurveDemo(card) {
  const dot = card.querySelector(".track > i")
  const track = card.querySelector(".track")
  const ease = css(card.querySelector("svg.curve").dataset.ease)
  const distance = track.clientWidth - 24
  dot.animate([{ transform: "translateX(0)" }, { transform: `translateX(${distance}px)` }], { duration: Math.max(900, ms("--dur-draw")), easing: ease, fill: "forwards" })
}

function durationLadder() {
  const names = ["--dur-instant", "--dur-fast-exit", "--dur-press", "--dur-exit", "--dur-fast", "--dur-base", "--dur-panel", "--dur-slow", "--dur-draw"]
  const host = document.getElementById("durs")
  host.innerHTML = names
    .map((name) => {
      const value = Number.parseFloat(getComputedStyle(document.body).getPropertyValue(name)) || 0
      return `<div class="dur-row"><span class="mono">${name}</span><i data-ms="${value}" style="transform:scaleX(${value / 900})"></i><span class="num note">${fmt.format(value)} мс</span></div>`
    })
    .join("")
}

function runLadder() {
  for (const bar of document.querySelectorAll("#durs i")) {
    const value = Number(bar.dataset.ms)
    bar.animate([{ transform: "scaleX(0)" }, { transform: `scaleX(${value / 900})` }], { duration: root.dataset.motion === "reduced" ? 1 : value, easing: css("--ease-out"), fill: "forwards" })
  }
}

const DEMOS = {
  enter: (stage) => stage.querySelectorAll(".mini-list > div").forEach((el) => replay(el, "anim-enter")),
  pop: (stage) => replay(stage.querySelector(".pop-target"), "anim-pop"),
  pin: (stage) => {
    replay(stage.querySelector(".pin-target"), "anim-pin")
  },
  draw: (stage) => stage.querySelectorAll(".draw-target").forEach((el) => replay(el, "anim-draw")),
  sheet: (stage) => replay(stage.querySelector(".sheet"), "anim"),
  swap: (stage) => {
    const values = ["Лето: 14 связей", "Зима: 9 связей", "Все сезоны: 23 связи"]
    const box = stage.querySelector(".swap-box")
    const index = (Number(box.dataset.i ?? 0) + 1) % values.length
    box.dataset.i = String(index)
    swapText(box, values[index])
  },
  skeleton: (stage) => {
    const skel = stage.querySelector(".skel-state")
    const content = stage.querySelector(".content-state")
    const spinner = stage.querySelector(".spin-state")
    skel.hidden = true
    content.hidden = true
    spinner.hidden = true
    const start = performance.now()
    const showSkel = setTimeout(() => {
      skel.hidden = false
    }, 200)
    setTimeout(() => {
      clearTimeout(showSkel)
      const shownFor = skel.hidden ? 300 : performance.now() - start - 200
      setTimeout(() => {
        skel.hidden = true
        content.hidden = false
        content.querySelectorAll(".mini-list > div").forEach((el) => replay(el, "anim-enter"))
      }, Math.max(0, 300 - shownFor))
    }, 900)
  },
  progress: (stage) => {
    const bar = stage.querySelector(".progress > i")
    const steps = [0.1, 0.35, 0.6, 0.85, 1]
    steps.forEach((value, index) => setTimeout(() => bar.style.setProperty("--p", String(value)), index * 380))
  },
  ladder: () => runLadder()
}

function initDemos() {
  document.querySelectorAll("[data-replay]").forEach((button) =>
    button.addEventListener("click", () => {
      const card = button.closest(".motion-card")
      const kind = button.dataset.replay
      if (kind === "curve") runCurveDemo(card)
      else DEMOS[kind]?.(card.querySelector(".stage") ?? card)
    }),
  )
  for (const path of document.querySelectorAll(".draw-target")) path.style.setProperty("--len", String(Math.ceil(path.getTotalLength())))
}

function bucket(count) {
  if (count === null || count === undefined) return null
  if (count === 0) return 1
  if (count <= 2) return 2
  if (count <= 5) return 3
  if (count <= 10) return 4
  if (count <= 20) return 5
  if (count <= 40) return 6
  return 7
}

function seasonCount(region, season) {
  const c = region.c ?? {}
  if (region.k === null || region.k === undefined) return null
  if (season === "summer") return (c.summer ?? 0) + (c.all ?? 0)
  if (season === "winter") return (c.winter ?? 0) + (c.all ?? 0)
  return region.k
}

function paintMap(svg, season) {
  for (const path of svg.querySelectorAll(".region")) {
    const region = REGIONS[Number(path.dataset.idx)]
    const step = bucket(seasonCount(region, season))
    path.style.fill = step === null ? "var(--map-none)" : `var(--seq-${step})`
  }
}

function buildMap(svg, interactive) {
  svg.setAttribute("viewBox", "30 50 935 525")
  svg.innerHTML = REGIONS.map((region, index) => `<path class="region" data-idx="${index}" d="${region.p}"${interactive ? ' tabindex="-1"' : ""}><title>${region.n}</title></path>`).join("")
}

function regionPanel(region, season) {
  const c = region.c ?? {}
  const count = seasonCount(region, season)
  const modes = Object.entries(c)
    .filter(([key]) => key.startsWith("m_"))
    .sort((a, b) => b[1] - a[1])
    .map(([key, value]) => {
      const mode = MODES[key.slice(2)]
      return mode ? `<div class="legend-row" style="--c:${mode.color}"><span class="mode-ico" style="--c:${mode.color}">${svgIcon(mode.icon, "s16")}</span><span>${mode.name}</span><span class="num" style="margin-left:auto">${fmt.format(value)}</span></div>` : ""
    })
    .join("")
  return `
    <nav class="crumbs" aria-label="Путь"><a href="#map">Россия</a>${svgIcon("chevron-right", "s16")}<span>${region.n}</span></nav>
    <h3 style="font-size:var(--fs-h2);line-height:1.15;font-weight:700;letter-spacing:-0.01em">${region.n}</h3>
    <div class="kv">
      <div class="stat"><span class="stat-label">Населённых пунктов</span><span class="stat-value num">${region.s === null || region.s === undefined ? "нет данных" : fmt.format(region.s)}</span></div>
      <div class="stat"><span class="stat-label">Связей в сезоне</span><span class="stat-value num">${count === null ? "нет данных" : fmt.format(count)}</span></div>
    </div>
    <div class="stack"><span class="stat-label">Индекс доступности</span><div class="row"><span class="badge neutral">${svgIcon("info")}Не подключён</span><span class="note">Региональный расчёт ещё не выгружен</span></div></div>
    <div class="stack"><span class="stat-label">Связи по видам транспорта</span>${modes || '<p class="note">В выгрузке нет ручных связей для этого региона.</p>'}</div>`
}

function initMap() {
  const svg = document.getElementById("map-svg")
  const tip = document.getElementById("map-tip")
  const panel = document.getElementById("map-panel")
  const frame = svg.closest(".mapframe")
  let season = "all"
  let active = null
  buildMap(svg, true)
  paintMap(svg, season)
  const seasonName = { all: "все сезоны", summer: "лето", winter: "зима" }
  svg.addEventListener("pointermove", (event) => {
    const path = event.target.closest(".region")
    if (!path) {
      tip.hidden = true
      return
    }
    const region = REGIONS[Number(path.dataset.idx)]
    const count = seasonCount(region, season)
    const box = frame.getBoundingClientRect()
    if (tip.hidden || tip.dataset.idx !== path.dataset.idx) {
      tip.innerHTML = `<b>${region.n}</b><div class="note">Связей, ${seasonName[season]}: <span class="num">${count === null ? "нет данных" : fmt.format(count)}</span></div>`
      tip.dataset.idx = path.dataset.idx
      if (tip.hidden) {
        tip.hidden = false
        replay(tip, "anim-pop")
      }
    }
    const x = Math.min(event.clientX - box.left + 14, box.width - tip.offsetWidth - 8)
    const y = Math.max(event.clientY - box.top - tip.offsetHeight - 12, 8)
    tip.style.transform = `translate(${x}px, ${y}px)`
  })
  svg.addEventListener("pointerleave", () => {
    tip.hidden = true
  })
  svg.addEventListener("click", (event) => {
    const path = event.target.closest(".region")
    if (!path) return
    if (active) active.dataset.active = "false"
    active = path
    path.dataset.active = "true"
    path.parentNode.append(path)
    panel.innerHTML = regionPanel(REGIONS[Number(path.dataset.idx)], season)
    panel.querySelectorAll(".kv, .stack, h3, .crumbs").forEach((el, index) => {
      el.style.setProperty("--i", String(index))
      replay(el, "anim-enter")
    })
  })
  document.getElementById("map-season").addEventListener("change", (event) => {
    season = event.detail
    paintMap(svg, season)
    if (active) panel.innerHTML = regionPanel(REGIONS[Number(active.dataset.idx)], season)
  })
  const search = document.getElementById("map-search")
  search.addEventListener("change", () => {
    const query = search.value.trim().toLowerCase()
    const index = REGIONS.findIndex((region) => region.n.toLowerCase().includes(query))
    if (index >= 0) svg.querySelector(`[data-idx="${index}"]`).dispatchEvent(new MouseEvent("click", { bubbles: true }))
  })
  document.getElementById("region-list").innerHTML = REGIONS.map((region) => `<option value="${region.n}"></option>`).join("")
}

function initDataTable() {
  const rows = [...REGIONS].filter((region) => region.k !== null && region.k !== undefined).sort((a, b) => b.k - a.k).slice(0, 6)
  const empty = REGIONS.find((region) => region.k === null || region.k === undefined)
  if (empty) rows.push(empty)
  document.getElementById("data-table").innerHTML = rows
    .map((region) => {
      const has = region.k !== null && region.k !== undefined
      const status = !has ? '<span class="badge neutral">' + svgIcon("info") + "Нет в выгрузке</span>" : region.k >= 20 ? '<span class="badge success">' + svgIcon("check") + "Собрано</span>" : '<span class="badge warning">' + svgIcon("warning") + "Неполно</span>"
      return `<tr class="row-hover"><td>${region.n}</td><td class="r num">${region.s === null || region.s === undefined ? "нет данных" : fmt.format(region.s)}</td><td class="r num">${has ? fmt.format(region.k) : "нет данных"}</td><td>${status}</td></tr>`
    })
    .join("")
}

function initOgMaps() {
  for (const svg of document.querySelectorAll("svg.og-map")) {
    buildMap(svg, false)
    paintMap(svg, svg.dataset.season ?? "all")
  }
}

function scaleOg() {
  for (const frame of document.querySelectorAll(".og-frame")) {
    const card = frame.querySelector(".og")
    card.style.setProperty("--k", String(frame.clientWidth / card.offsetWidth))
  }
}

function initMotionToggle() {
  const seg = document.getElementById("motion-seg")
  seg.addEventListener("change", (event) => {
    root.dataset.motion = event.detail
    durationLadder()
  })
}

function initNav() {
  const links = [...document.querySelectorAll(".nav a")]
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue
        links.forEach((link) => link.setAttribute("aria-current", String(link.hash === `#${entry.target.id}`)))
      }
    },
    { rootMargin: "-30% 0px -60% 0px" },
  )
  document.querySelectorAll("main > section").forEach((section) => observer.observe(section))
}

function initContrastTable() {
  for (const row of document.querySelectorAll("[data-contrast]")) {
    const [fg, bg] = row.dataset.contrast.split("|")
    const value = contrast(css(fg), css(bg))
    const cell = row.querySelector(".cr")
    const min = Number(row.dataset.min ?? 4.5)
    const ok = value >= min
    cell.innerHTML = `<span class="contrast ${ok ? "ok" : "bad"}" title="Норма ${String(min).replace(".", ",")} : 1">${svgIcon(ok ? "check" : "close", "s16")}${value.toFixed(2).replace(".", ",")} : 1</span>`
  }
}

function hexLum(hex) {
  const value = hex.replace("#", "")
  const channels = [0, 2, 4].map((i) => Number.parseInt(value.slice(i, i + 2), 16) / 255)
  const linear = channels.map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
}

function contrast(a, b) {
  const [hi, lo] = [hexLum(resolveHex(a)), hexLum(resolveHex(b))].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

function resolveHex(value) {
  const match = /var\((--[\w-]+)\)/.exec(value)
  return match ? resolveHex(css(match[1])) : value
}

const TONES = {
  light: { ink: "#0e1012", stops: ["#0066db", "#b9d5f8"] },
  dark: { ink: "#ffffff", stops: ["#5aa6ff", "#1d4f8f"] },
  blue: { ink: "#ffffff", stops: ["#ffffff", "#7fb0ee"] },
  "wrong-ink": { ink: "#0066db", stops: ["#0066db", "#b9d5f8"] },
  "wrong-order": { ink: "#0e1012", stops: ["#b9d5f8", "#0066db"] },
  broken: { ink: "#0e1012", stops: ["#0066db", "#b9d5f8"], dash: true },
}

function mixHex(a, b, t) {
  const pa = [1, 3, 5].map((i) => Number.parseInt(a.slice(i, i + 2), 16))
  const pb = [1, 3, 5].map((i) => Number.parseInt(b.slice(i, i + 2), 16))
  return `#${pa.map((v, i) => Math.round(v + (pb[i] - v) * t).toString(16).padStart(2, "0")).join("")}`
}

function markMarkup(kind, tone) {
  const m = MARK[kind]
  const t = TONES[tone] ?? TONES.light
  const n = m.rings.length
  const rings = m.rings.map((d, k) => `<path class="bm-ring" data-k="${k}" fill="${mixHex(t.stops[0], t.stops[1], n > 1 ? k / (n - 1) : 0)}" fill-rule="evenodd" d="${d}"${t.dash && k === n - 1 ? ' style="clip-path:inset(0 0 0 52%)"' : ""}/>`).join("")
  return `<svg viewBox="${m.viewBox}" aria-hidden="true">${rings}<path class="bm-word" fill="${t.ink}" fill-rule="evenodd" d="${m.word}"/></svg>`
}

function mountMarks() {
  document.querySelectorAll("[data-mark]").forEach((el) => {
    el.innerHTML = markMarkup(el.dataset.mark, el.dataset.tone)
  })
}

function animateMark(scope) {
  const step = Math.max(ms("--stagger"), 0) * 3
  scope.querySelectorAll(".bm-word").forEach((el) => {
    el.animate([{ opacity: 0, transform: "translateY(4px)" }, { opacity: 1, transform: "none" }], { duration: ms("--dur-slow"), easing: css("--ease-out"), fill: "backwards" })
  })
  scope.querySelectorAll(".bm-ring").forEach((el) => {
    el.style.transformBox = "fill-box"
    el.style.transformOrigin = "center"
    el.animate([{ opacity: 0, transform: "scale(0.96)" }, { opacity: 1, transform: "none" }], { duration: ms("--dur-slow") * 2, delay: ms("--dur-base") + Number(el.dataset.k) * step, easing: css("--ease-out"), fill: "backwards" })
  })
}

function pulseMarks() {
  if (ms("--dur-slow") <= 1) return
  document.querySelectorAll(".brand-mark.pulse .bm-ring").forEach((el) => {
    el.animate([{ opacity: 1 }, { opacity: 0.2 }, { opacity: 1 }], { duration: ms("--dur-draw") * 1.6, delay: Number(el.dataset.k) * ms("--dur-base"), iterations: Number.POSITIVE_INFINITY, easing: css("--ease-in-out") })
  })
}

mountMarks()
animateMark(document.querySelector(".top"))
animateMark(document.getElementById("brand-hero"))
pulseMarks()
document.getElementById("brand-hero").addEventListener("click", (event) => animateMark(event.currentTarget))
document.getElementById("brand-replay").addEventListener("click", () => animateMark(document.getElementById("brand-intro")))
initIsolines()
paintIcons()
iconGallery()
initSegs()
initTabs()
initToggles()
initTooltips()
initPopover()
initDialog()
initToasts()
initPending()
initDisclosure()
initScenario()
drawCurves()
durationLadder()
initDemos()
initMap()
initDataTable()
initOgMaps()
initMotionToggle()
initNav()
initContrastTable()
scaleOg()
addEventListener("resize", scaleOg)
document.fonts?.ready.then(() => {
  document.querySelectorAll(".seg").forEach(placeSeg)
  document.querySelectorAll(".tabs").forEach(placeTabs)
})

function blobPath(cx, cy, r, seed, wob = 0.12) {
  const pts = []
  for (let i = 0; i <= 72; i += 1) {
    const a = (i / 72) * Math.PI * 2
    const k = 1 + wob * Math.sin(3 * a + seed) + wob * 0.5 * Math.sin(5 * a + seed * 1.7) + wob * 0.3 * Math.cos(2 * a + seed * 0.6)
    pts.push(`${(cx + Math.cos(a) * r * k).toFixed(1)} ${(cy + Math.sin(a) * r * k * 0.86).toFixed(1)}`)
  }
  return `M${pts.join("L")}Z`
}

function drawRings(svg, rings, play = true) {
  svg.querySelectorAll(".iso-r").forEach((el) => {
    el.setAttribute("pathLength", "1")
  })
  if (!play || ms("--dur-slow") <= 1) return
  svg.querySelectorAll(".iso-r").forEach((el, i) => {
    el.style.transformBox = "fill-box"
    el.style.transformOrigin = "center"
    el.animate([{ opacity: 0, transform: "scale(0.85)" }, { opacity: 1, transform: "none" }], { duration: ms("--dur-slow") * 2, delay: i * ms("--dur-base") * 0.6, easing: css("--ease-out"), fill: "backwards" })
  })
}

function initIsolines() {
  const point = document.getElementById("iso-point")
  const drawPoint = () => {
    const cx = 170
    const cy = 120
    const radii = [34, 62, 96]
    const labels = ["1 ч", "2 ч", "4 ч"]
    const rings = radii.map((r, i) => `<path class="iso-r k${i + 1}" d="${blobPath(cx, cy, r, 1.3 + i * 0.4)}"/>`).reverse().join("")
    const tags = radii.map((r, i) => `<text class="iso-tag" x="${cx + r * 0.62}" y="${cy - r * 0.62 + 4}">${labels[i]}</text>`).join("")
    point.innerHTML = `<svg class="iso-svg" viewBox="0 0 340 240" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><path d="M-60 190c60-20 120 10 180-6s110-30 280-8V260H-60Z" fill="var(--map-water)"/>${rings}${tags}<circle cx="${cx}" cy="${cy}" r="6" fill="var(--iso-1)" stroke="#fff" stroke-width="2.5"/></svg>`
    drawRings(point.querySelector("svg"))
  }
  drawPoint()
  point.addEventListener("click", drawPoint)

  const region = document.getElementById("iso-region")
  const tuva = REGIONS.find((r) => r.n.includes("Тыва")) ?? REGIONS[0]
  const drawRegion = () => {
    region.innerHTML = `<svg class="iso-svg" aria-hidden="true"><g class="reg"><path class="iso-k" d="${tuva.p}" fill="none" stroke="var(--iso-3)" stroke-width="15" stroke-linejoin="round"/><path class="iso-k" d="${tuva.p}" fill="none" stroke="var(--map-land)" stroke-width="13" stroke-linejoin="round"/><path class="iso-k" d="${tuva.p}" fill="none" stroke="var(--iso-2)" stroke-width="10" stroke-linejoin="round"/><path class="iso-k" d="${tuva.p}" fill="none" stroke="var(--map-land)" stroke-width="8" stroke-linejoin="round"/><path class="iso-k" d="${tuva.p}" fill="none" stroke="var(--iso-1)" stroke-width="5" stroke-linejoin="round"/><path d="${tuva.p}" fill="var(--seq-4)" stroke="var(--map-land)" stroke-width="3" stroke-linejoin="round" paint-order="stroke"/></g></svg>`
    const svg = region.querySelector("svg")
    const b = svg.querySelector(".reg").getBBox()
    const pad = 14
    svg.setAttribute("viewBox", `${b.x - pad} ${b.y - pad} ${b.width + pad * 2} ${b.height + pad * 2}`)
    if (ms("--dur-slow") <= 1) return
    svg.querySelectorAll(".iso-k").forEach((el, i) => {
      el.animate([{ strokeWidth: "0px" }, { strokeWidth: getComputedStyle(el).strokeWidth }], { duration: ms("--dur-slow") * 2, delay: (4 - i) * ms("--dur-base") * 0.4, easing: css("--ease-out"), fill: "backwards" })
    })
  }
  drawRegion()
  region.addEventListener("click", drawRegion)

  const scn = document.getElementById("iso-scenario")
  const scnSvg = scn.querySelector("svg")
  let grown = false
  const renderScn = () => {
    const radii = grown ? [36, 64, 96] : [30, 50, 70]
    scnSvg.innerHTML = radii.map((r, i) => `<path class="iso-r k${i + 1}" d="${blobPath(110, 100, r, 0.8 + i * 0.5, 0.1)}"/>`).reverse().join("")
    drawRings(scnSvg)
    document.getElementById("iso-scn-value").textContent = grown ? "5" : "2"
    document.getElementById("iso-scn-label").textContent = grown ? "С новым рейсом" : "Базовый вариант"
    document.querySelector("#iso-scn-btn .btn-label").textContent = grown ? "Убрать рейс" : "Добавить рейс"
  }
  renderScn()
  document.getElementById("iso-scn-btn").addEventListener("click", () => {
    grown = !grown
    renderScn()
  })

  const hover = document.getElementById("iso-hover")
  const dotsXY = [[70, 80], [150, 60], [230, 110], [110, 160], [200, 180], [280, 70]]
  hover.innerHTML = `<svg class="iso-svg" viewBox="0 0 340 240" preserveAspectRatio="xMidYMid slice" aria-hidden="true">${dotsXY.map(([x, y]) => `<g class="hv" data-x="${x}" data-y="${y}"><circle cx="${x}" cy="${y}" r="16" fill="transparent"/><circle cx="${x}" cy="${y}" r="5.5" fill="var(--text-primary)" stroke="#fff" stroke-width="2"/></g>`).join("")}</svg>`
  hover.querySelectorAll(".hv").forEach((g) => {
    g.addEventListener("pointerenter", () => {
      if (ms("--dur-slow") <= 1) return
      const ring = document.createElementNS("http://www.w3.org/2000/svg", "circle")
      ring.setAttribute("cx", g.dataset.x)
      ring.setAttribute("cy", g.dataset.y)
      ring.setAttribute("r", "18")
      ring.setAttribute("class", "iso-r k1")
      ring.style.transformBox = "fill-box"
      ring.style.transformOrigin = "center"
      g.prepend(ring)
      ring.animate([{ opacity: 0.9, transform: "scale(0.3)" }, { opacity: 0, transform: "scale(1.4)" }], { duration: ms("--dur-draw"), easing: css("--ease-out"), fill: "forwards" }).finished.then(() => ring.remove())
    })
  })

  const halo = document.querySelector(".iso-halo svg")
  halo.innerHTML = [58, 46, 34].map((r, i) => `<circle class="iso-r k${3 - i}" cx="60" cy="60" r="${r}" style="stroke-width:1.5px"/>`).join("")
  drawRings(halo)

  const cover = document.querySelector(".iso-cover svg")
  cover.innerHTML = [60, 100, 140, 180, 220].map((r, i) => `<path class="iso-r ${i < 2 ? "k2" : "k3"}" d="${blobPath(300, 10, r, 2 + i * 0.3, 0.07)}" style="stroke-width:1.5px"/>`).join("")
  drawRings(cover)
}
