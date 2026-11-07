const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches
const EASE = "cubic-bezier(0.23, 1, 0.32, 1)"
const EASE_IO = "cubic-bezier(0.77, 0, 0.175, 1)"
const STORE = "plexus-marks"
const ICON = {
  replay: '<svg viewBox="0 0 24 24"><path d="M20 12a8 8 0 1 1-2.6-5.9"/><path d="M20.5 4v4.5H16"/></svg>',
  star: '<svg viewBox="0 0 24 24"><path d="m12 3.5 2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8L3.5 9.7l5.9-.9Z"/></svg>',
  grid: '<svg viewBox="0 0 24 24"><path d="M4 4h16v16H4zM4 12h16M12 4v16M4 4l16 16"/></svg>',
}

const store = (() => {
  try {
    return JSON.parse(localStorage.getItem(STORE) ?? "{}")
  } catch {
    return {}
  }
})()
const state = { favs: store.favs ?? [], filter: "all", grid: false }
const save = () => {
  try {
    localStorage.setItem(STORE, JSON.stringify({ favs: state.favs }))
  } catch {
    return
  }
}

function svgOf(spec, cls) {
  return `<svg class="m ${cls}" viewBox="${spec.vb}" aria-hidden="true">${spec.body}</svg>`
}

function mount(host, spec, cls, style = "") {
  host.insertAdjacentHTML("beforeend", svgOf(spec, cls).replace("<svg ", `<svg style="${style}" `))
  const svg = host.lastElementChild
  spec.build?.(svg)
  svg.querySelectorAll('[data-a="draw"]').forEach((el) => el.setAttribute("pathLength", "1"))
  return svg
}

function lockupInto(host, concept, variant = "mark") {
  const spec = variant === "alt" ? concept.alt() : concept.mark()
  const wrap = document.createElement("span")
  wrap.className = "lockup"
  host.append(wrap)
  if (concept.word) {
    mount(wrap, spec, "word")
  } else {
    mount(wrap, spec, "mark")
    wrap.insertAdjacentHTML("beforeend", '<span class="wordmark">plexus</span>')
  }
  return wrap
}

function animate(scope) {
  for (const el of scope.querySelectorAll("[data-a]")) {
    const kind = el.dataset.a
    const delay = reduced ? 0 : Number(el.dataset.o ?? 0) * Number(el.dataset.step ?? 120)
    const base = { duration: reduced ? 1 : 620, delay, easing: EASE, fill: "backwards" }
    el.style.transformBox = "fill-box"
    el.style.transformOrigin = "center"
    if (kind === "draw") el.animate([{ strokeDasharray: "1 1", strokeDashoffset: 1 }, { strokeDasharray: "1 1", strokeDashoffset: 0 }], { ...base, duration: reduced ? 1 : 760, easing: EASE_IO })
    else if (kind === "pop") el.animate([{ opacity: 0, transform: "scale(0.2)" }, { opacity: 1, transform: "scale(1)" }], { ...base, duration: reduced ? 1 : 420 })
    else if (kind === "fade") el.animate([{ opacity: 0 }, { opacity: 1 }], { ...base, duration: reduced ? 1 : 260 })
    else if (kind === "slideX") el.animate([{ opacity: 0, transform: "translateX(-24px)" }, { opacity: 1, transform: "none" }], base)
    else if (kind === "slideY") el.animate([{ opacity: 0, transform: "translateY(-24px)" }, { opacity: 1, transform: "none" }], base)
    else if (kind === "slideL") el.animate([{ opacity: 0, transform: "translateX(-14px)" }, { opacity: 1, transform: "none" }], base)
    else if (kind === "slideR") el.animate([{ opacity: 0, transform: "translateX(14px)" }, { opacity: 1, transform: "none" }], base)
    else if (kind === "unfold") {
      el.style.transformBox = "view-box"
      el.style.transformOrigin = "50px 50px"
      el.animate([{ opacity: 0, transform: "scale(0.4) rotate(-12deg)" }, { opacity: 1, transform: "none" }], { ...base, duration: reduced ? 1 : 700 })
    } else if (kind === "ring") el.animate([{ strokeWidth: 0 }, { strokeWidth: el.dataset.w }], { ...base, duration: reduced ? 1 : 900 })
  }
}

function guides(svg) {
  const [x, y, w, h] = svg.getAttribute("viewBox").split(/\s+/).map(Number)
  const step = w > 150 ? 20 : 10
  const lines = []
  for (let gx = Math.ceil(x / step) * step; gx <= x + w; gx += step) lines.push(`M${gx} ${y}V${y + h}`)
  for (let gy = Math.ceil(y / step) * step; gy <= y + h; gy += step) lines.push(`M${x} ${gy}H${x + w}`)
  if (w <= 150) lines.push(`M${x} ${y}L${x + w} ${y + h}M${x + w} ${y}L${x} ${y + h}`)
  svg.insertAdjacentHTML("beforeend", `<g class="guides"><path d="${lines.join("")}"/></g>`)
}

function plate(concept) {
  const el = document.createElement("article")
  el.className = "plate"
  el.dataset.n = concept.n
  const fav = state.favs.includes(concept.n)
  el.innerHTML = `
    <div class="specimen ctx ${concept.bg}" role="button" tabindex="0" aria-label="Повторить анимацию">
      <span class="replay">Клик повторяет анимацию</span>
    </div>
    <div class="notes">
      <span class="kicker">Концепция ${concept.n} из ${CONCEPTS.length}</span>
      <h2>${concept.title}</h2>
      <p class="idea">${concept.idea}</p>
      <dl><dt>Сильная сторона</dt><dd>${concept.plus}</dd><dt>Риск</dt><dd>${concept.risk}</dd></dl>
      <div class="apps">
        <div class="apps-row">
          <div class="swatch ctx" data-small></div>
          <div class="swatch ctx ink" data-small></div>
        </div>
        <div class="apps-row">
          <div class="icon-tile ctx blue" data-icon></div>
          <div class="icon-tile ctx ink" data-icon></div>
          <div class="tabmock ctx" data-tab><span>Plexus</span></div>
        </div>
        <div class="header-mock ctx" data-header><nav><span>Карта</span><span>Регионы</span><span>Сценарии</span></nav></div>
      </div>
      <div class="actions">
        <button type="button" class="btn star" aria-pressed="${fav}">${ICON.star}${fav ? "В избранном" : "В избранное"}</button>
        <button type="button" class="btn replay-btn">${ICON.replay}Повторить</button>
      </div>
    </div>`
  return el
}

function fill(el, concept) {
  const specimen = el.querySelector(".specimen")
  lockupInto(specimen, concept)
  if (concept.alt) {
    const row = document.createElement("div")
    row.className = "alt-row"
    row.innerHTML = "<span>Одноцветная версия</span>"
    specimen.append(row)
    mount(row, concept.alt(), "word")
  }
  el.querySelectorAll("[data-small]").forEach((box) => [16, 24, 32, 48].forEach((s) => mount(box, concept.small(), "", `width:${s}px;height:${s}px`)))
  el.querySelectorAll("[data-icon]").forEach((box) => mount(box, concept.small(), ""))
  mount(el.querySelector("[data-tab]"), concept.small(), "")
  el.querySelector("[data-tab]").prepend(el.querySelector("[data-tab] svg"))
  const header = el.querySelector("[data-header]")
  const lk = lockupInto(header, concept)
  header.prepend(lk)
  if (concept.word) lk.querySelector("svg").style.cssText = "height:34px;width:auto"
  else lk.style.fontSize = "22px"
}

function render() {
  const host = document.getElementById("plates")
  host.innerHTML = ""
  const list = state.filter === "fav" ? CONCEPTS.filter((c) => state.favs.includes(c.n)) : CONCEPTS
  list.forEach((concept) => {
    const el = plate(concept)
    host.append(el)
    fill(el, concept)
  })
  document.getElementById("empty").hidden = list.length > 0
  document.getElementById("fav-count").textContent = state.favs.length ? ` ${state.favs.length}` : ""
  if (state.grid) document.querySelectorAll(".specimen svg").forEach(guides)
  host.querySelectorAll(".specimen").forEach((spec) => io.observe(spec))
}

const io = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue
      io.unobserve(entry.target)
      animate(entry.target)
      animate(entry.target.closest(".plate").querySelector("[data-header]"))
    }
  },
  { threshold: 0.4 },
)

document.getElementById("plates").addEventListener("click", (event) => {
  const plateEl = event.target.closest(".plate")
  if (!plateEl) return
  const n = Number(plateEl.dataset.n)
  const star = event.target.closest(".star")
  if (star) {
    state.favs = state.favs.includes(n) ? state.favs.filter((v) => v !== n) : [...state.favs, n]
    save()
    const on = state.favs.includes(n)
    star.setAttribute("aria-pressed", String(on))
    star.innerHTML = `${ICON.star}${on ? "В избранном" : "В избранное"}`
    document.getElementById("fav-count").textContent = state.favs.length ? ` ${state.favs.length}` : ""
    if (state.filter === "fav" && !on) render()
    return
  }
  if (event.target.closest(".specimen") || event.target.closest(".replay-btn")) animate(plateEl)
})

document.getElementById("plates").addEventListener("keydown", (event) => {
  const spec = event.target.closest(".specimen")
  if (spec && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault()
    animate(spec)
  }
})

document.querySelectorAll("[data-filter]").forEach((button) =>
  button.addEventListener("click", () => {
    state.filter = button.dataset.filter
    document.querySelectorAll("[data-filter]").forEach((b) => b.setAttribute("aria-pressed", String(b === button)))
    render()
  }),
)

document.getElementById("grid-toggle").addEventListener("click", (event) => {
  state.grid = !state.grid
  event.currentTarget.setAttribute("aria-pressed", String(state.grid))
  if (state.grid) document.querySelectorAll(".specimen svg").forEach(guides)
  else document.querySelectorAll(".guides").forEach((g) => g.remove())
})

document.getElementById("replay-all").addEventListener("click", () => document.querySelectorAll(".plate").forEach(animate))

document.fonts.ready.then(render)
