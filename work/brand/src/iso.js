const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches
const EASE = "cubic-bezier(0.23, 1, 0.32, 1)"
const BG = { white: "#ffffff", land: "#f3efe7", dark: "#0e1012", blue: "#0066db" }
const INK = { white: "#0e1012", land: "#0e1012", dark: "#ffffff", blue: "#ffffff" }
const SCHEMES = {
  blue: { name: "Синий", stops: ["#6aa6f0"] },
  grade: { name: "Синий градацией", stops: ["#0066db", "#b9d5f8"] },
  teal: { name: "Цвета карты", stops: ["#2b6b85", "#9fd0c4"] },
  ink: { name: "Графит", stops: ["#0e1012"] },
  modes: { name: "Виды транспорта", stops: ["#7a5af5", "#0b8fb0", "#d0752b"], discrete: true },
  night: { name: "Ночной", stops: ["#5aa6ff", "#1d4f8f"] },
  snow: { name: "Белый", stops: ["#ffffff", "#8fbaf2"] },
}
const ANIMS = { wave: "Волна от букв", word: "Слово, потом кольца", pulse: "Пульс, как загрузка" }

const VARIANTS = [
  { n: 1, title: "Базовый", note: "Три ровных кольца, как в первой версии.", p: { rings: 3, step: 6.5, line: 2, gap: 11, scheme: "blue", weight: 700, track: -2, bg: "white" } },
  { n: 2, title: "Градация", note: "Ближнее кольцо насыщеннее: чем ближе, тем доступнее.", p: { rings: 3, step: 6.5, line: 2.2, gap: 11, scheme: "grade", weight: 700, track: -2, bg: "white" } },
  { n: 3, title: "Плотный", note: "Четыре тонких кольца близко, жирные буквы.", p: { rings: 4, step: 4.6, line: 1.5, gap: 9.5, scheme: "grade", weight: 800, track: -3, bg: "white" } },
  { n: 4, title: "Воздушный", note: "Два кольца с большим шагом, лёгкие буквы.", p: { rings: 2, step: 9, line: 2.4, gap: 12, scheme: "blue", weight: 600, track: -1, bg: "white" } },
  { n: 5, title: "Зоны заливкой", note: "Как на карте доступности: зоны залиты, без контуров.", p: { rings: 3, step: 7, line: 0, gap: 7, scheme: "grade", weight: 700, track: -2, bg: "white", fill: true } },
  { n: 6, title: "Сезонный", note: "Внешнее кольцо пунктиром: доступ, который есть не круглый год.", p: { rings: 3, step: 6.5, line: 2, gap: 11, scheme: "grade", weight: 700, track: -2, bg: "white", dash: true } },
  { n: 7, title: "Гравюра", note: "Пять тонких графитовых колец, как на старой топокарте.", p: { rings: 5, step: 3.8, line: 1, gap: 9, scheme: "ink", weight: 700, track: -2, bg: "white" } },
  { n: 8, title: "Виды транспорта", note: "Кольца цветами транспорта: авиа, река, паром.", p: { rings: 3, step: 6.5, line: 2.2, gap: 11, scheme: "modes", weight: 700, track: -2, bg: "white" } },
  { n: 9, title: "Ночь", note: "Тёмный фон, кольца светятся от букв наружу.", p: { rings: 3, step: 6.5, line: 2, gap: 11, scheme: "night", weight: 700, track: -2, bg: "dark" } },
  { n: 10, title: "На синем", note: "Белое слово на фирменном синем, для обложки и иконки.", p: { rings: 3, step: 6.5, line: 2, gap: 11, scheme: "snow", weight: 700, track: -2, bg: "blue" } },
  { n: 11, title: "Одно кольцо", note: "Одно толстое кольцо, почти наклейка. Самый простой в производстве.", p: { rings: 1, step: 6, line: 3.6, gap: 10, scheme: "grade", weight: 800, track: -3, bg: "white" } },
  { n: 12, title: "Тёплая карта", note: "Бумажный фон и цвета данных из палитры карты.", p: { rings: 3, step: 6.5, line: 2, gap: 11, scheme: "teal", weight: 700, track: -2, bg: "land" } },
]

const hex = (h) => [1, 3, 5].map((i) => Number.parseInt(h.slice(i, i + 2), 16))
const toHex = (rgb) => `#${rgb.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("")}`
function colorAt(schemeKey, k, n) {
  const s = SCHEMES[schemeKey]
  if (s.stops.length === 1) return s.stops[0]
  if (s.discrete) return s.stops[Math.min(k, s.stops.length - 1)]
  const t = n <= 1 ? 0 : k / (n - 1)
  const pos = t * (s.stops.length - 1)
  const i = Math.min(Math.floor(pos), s.stops.length - 2)
  const a = hex(s.stops[i])
  const b = hex(s.stops[i + 1])
  const f = pos - i
  return toHex(a.map((v, j) => v + (b[j] - v) * f))
}

function layers(p) {
  const bg = BG[p.bg]
  const out = []
  for (let k = p.rings - 1; k >= 0; k -= 1) {
    const d = p.gap + p.step * k
    const color = colorAt(p.scheme, k, p.rings)
    if (p.fill) {
      out.push({ k, w: 2 * (d + p.step / 2), color, kind: "ring" })
    } else {
      out.push({ k, w: 2 * (d + p.line / 2), color, kind: "ring", dash: p.dash && k === p.rings - 1 })
      out.push({ k, w: 2 * Math.max(d - p.line / 2, 0), color: bg, kind: "gap" })
    }
  }
  return out
}

function wordSvg(p, text = "plexus", size = 76) {
  const attrs = `x="0" y="0" font-size="${size}" font-weight="${p.weight}" letter-spacing="${p.track}"`
  const rings = layers(p)
    .map((l) => `<text class="iso-l" data-k="${l.k}" data-kind="${l.kind}" data-w="${f2(l.w)}" ${attrs} style="stroke:${l.color};stroke-width:${f2(l.w)}px${l.dash ? `;stroke-dasharray:${f2(l.w * 0.16)} ${f2(l.w * 0.12)}` : ""}">${text}</text>`)
    .join("")
  const knock = p.fill ? 2 * Math.max(p.gap - p.step / 2, 2) : 2 * Math.max(p.gap - p.line / 2, 0) - 0.5
  return `<svg class="iso" aria-hidden="true"><g class="iso-g">${rings}<text class="iso-word" ${attrs} style="fill:${INK[p.bg]};stroke:${BG[p.bg]};stroke-width:${f2(Math.max(knock, 0))}px">${text}</text></g></svg>`
}

function f2(n) {
  return Math.round(n * 100) / 100
}

function reach(p) {
  return p.gap + p.step * (p.rings - 1) + (p.fill ? p.step / 2 : p.line / 2) + 1
}

function fit(svg, p, pad = 0) {
  const word = svg.querySelector(".iso-word")
  const b = word.getBBox()
  const r = reach(p) + pad
  svg.setAttribute("viewBox", `${f2(b.x - r)} ${f2(b.y - r)} ${f2(b.width + 2 * r)} ${f2(b.height + 2 * r)}`)
}

function mountWord(host, p, opts = {}) {
  host.insertAdjacentHTML("beforeend", wordSvg(p, opts.text, opts.size))
  const svg = host.lastElementChild
  fit(svg, p, opts.pad ?? 0)
  return svg
}

function animate(svg, kind = state.anim, loop = false) {
  const rings = [...svg.querySelectorAll(".iso-l")]
  const word = svg.querySelector(".iso-word")
  if (reduced) return
  const base = kind === "word" ? 360 : 0
  if (kind === "word") word.animate([{ opacity: 0, transform: "translateY(6px)" }, { opacity: 1, transform: "none" }], { duration: 420, easing: EASE, fill: "backwards" })
  if (kind === "pulse") {
    rings
      .filter((el) => el.dataset.kind === "ring")
      .forEach((el) => {
        const k = Number(el.dataset.k)
        el.animate([{ opacity: 1 }, { opacity: 0.2 }, { opacity: 1 }], { duration: 1500, delay: k * 220, iterations: loop ? Number.POSITIVE_INFINITY : 2, easing: "ease-in-out" })
      })
    return
  }
  rings.forEach((el) => {
    const k = Number(el.dataset.k)
    el.animate([{ strokeWidth: "0px" }, { strokeWidth: `${el.dataset.w}px` }], { duration: 760, delay: base + k * 150, easing: EASE, fill: "backwards" })
  })
}

function smallMarks(p) {
  const sp = { ...p, gap: Math.max(p.gap * 0.9, 7), step: p.step * 1.05, line: Math.max(p.line * 1.6, p.fill ? 0 : 3), weight: 800, track: 0 }
  return [
    { key: "x", label: "Буква x" },
    { key: "p", label: "Буква p" },
    { key: "px", label: "Монограмма px" },
  ].map((m) => ({ ...m, p: { ...sp, rings: Math.min(p.rings, m.key === "px" ? 2 : 3) } }))
}

const store = (() => {
  try {
    return JSON.parse(localStorage.getItem("plexus-iso") ?? "{}")
  } catch {
    return {}
  }
})()
const state = {
  variant: store.variant ?? 2,
  p: store.p ?? { ...VARIANTS[1].p },
  anim: store.anim ?? "wave",
  favs: store.favs ?? [],
}
const save = () => {
  try {
    localStorage.setItem("plexus-iso", JSON.stringify({ variant: state.variant, p: state.p, anim: state.anim, favs: state.favs }))
  } catch {
    return
  }
}

function renderHero(play = true) {
  const host = document.getElementById("hero")
  host.innerHTML = ""
  host.style.background = BG[state.p.bg]
  const svg = mountWord(host, state.p, { pad: 6 })
  if (play) animate(svg)
  document.getElementById("params").textContent = summary(state.p)
  const v = VARIANTS.find((item) => item.n === state.variant)
  const changed = v && JSON.stringify(v.p) !== JSON.stringify(state.p)
  document.getElementById("hero-title").textContent = v ? `Вариант ${v.n}: ${v.title}${changed ? ", изменён" : ""}` : "Свой вариант"
  renderSmall()
  renderContext()
  syncControls()
  save()
}

function summary(p) {
  const parts = [`колец ${p.rings}`, `шаг ${p.step}`, p.fill ? "заливка" : `линия ${p.line}`, `отступ ${p.gap}`, `цвет «${SCHEMES[p.scheme].name}»`, `вес ${p.weight}`, `трекинг ${p.track}`]
  if (p.dash) parts.push("внешнее пунктиром")
  return parts.join(", ")
}

function renderSmall() {
  const host = document.getElementById("small")
  host.innerHTML = ""
  for (const m of smallMarks(state.p)) {
    const row = document.createElement("div")
    row.className = "small-row"
    row.innerHTML = `<span class="small-label">${m.label}</span><div class="small-sizes"></div><div class="small-tiles"></div>`
    host.append(row)
    const sizes = row.querySelector(".small-sizes")
    for (const s of [16, 24, 32, 48, 72]) {
      const box = document.createElement("span")
      box.className = "size-box"
      box.style.background = BG[state.p.bg]
      sizes.append(box)
      const rings = s <= 24 ? 1 : s <= 48 ? Math.min(2, m.p.rings) : m.p.rings
      const sp = s <= 24 ? { ...m.p, rings, gap: 7, line: Math.max(m.p.line, 4), step: 6 } : { ...m.p, rings }
      const svg = mountWord(box, sp, { text: m.key, size: 80 })
      svg.style.width = `${s}px`
      svg.style.height = `${s}px`
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet")
    }
    const tiles = row.querySelector(".small-tiles")
    for (const bg of ["blue", "dark"]) {
      const tile = document.createElement("span")
      tile.className = "app-tile"
      tile.style.background = BG[bg]
      tiles.append(tile)
      mountWord(tile, { ...m.p, bg, scheme: bg === "blue" ? "snow" : "night" }, { text: m.key, size: 80 })
    }
  }
}

function renderContext() {
  const p = state.p
  const tab = document.getElementById("ctx-tab")
  tab.innerHTML = ""
  const fav = mountWord(tab, { ...smallMarks(p)[0].p, rings: 1, gap: 7, line: 4, step: 6 }, { text: "x", size: 80 })
  fav.style.cssText = "width:16px;height:16px;background:transparent"
  tab.insertAdjacentHTML("beforeend", "<span>Plexus | Куда можно доехать и что изменится без связи</span>")

  const head = document.getElementById("ctx-head")
  head.innerHTML = ""
  const hw = mountWord(head, { ...p, bg: "white", scheme: p.bg === "dark" || p.bg === "blue" ? "grade" : p.scheme })
  hw.style.height = "40px"
  head.insertAdjacentHTML("beforeend", '<nav><b>Карта</b><span>Регионы</span><span>Сценарии</span></nav><span class="search"></span>')

  const og = document.getElementById("ctx-og")
  og.innerHTML = ""
  og.style.background = BG[p.bg]
  og.style.color = INK[p.bg]
  const ow = mountWord(og, p, { pad: 4 })
  ow.classList.add("og-word")
  og.insertAdjacentHTML("beforeend", '<p class="og-line">Куда можно доехать и что изменится без связи</p>')

  const deck = document.getElementById("ctx-deck")
  deck.innerHTML = ""
  const dp = { ...p, bg: "dark", scheme: "night" }
  deck.style.background = BG.dark
  const dw = mountWord(deck, dp, { pad: 4 })
  dw.classList.add("deck-word")
  deck.insertAdjacentHTML("beforeend", '<p class="deck-line">Индекс транспортной связанности</p>')

  const loader = document.getElementById("ctx-loader")
  loader.innerHTML = ""
  const lw = mountWord(loader, smallMarks(p)[0].p, { text: "x", size: 80 })
  lw.style.cssText = "width:72px;height:72px"
  loader.insertAdjacentHTML("beforeend", "<span>Пересчитываем индекс</span>")
  animate(lw, "pulse", true)
  ;[ow, dw, hw].forEach((svg) => animate(svg, state.anim))
}

function renderVariants() {
  const host = document.getElementById("variants")
  host.innerHTML = ""
  for (const v of VARIANTS) {
    const card = document.createElement("article")
    card.className = `vcard${v.n === state.variant ? " on" : ""}`
    card.dataset.n = v.n
    const fav = state.favs.includes(v.n)
    card.innerHTML = `<button type="button" class="vpick" aria-label="Открыть вариант ${v.n}"><span class="vprev" style="background:${BG[v.p.bg]}"></span></button><div class="vmeta"><b>${v.n}. ${v.title}</b><span>${v.note}</span></div><button type="button" class="star" aria-pressed="${fav}" aria-label="В избранное"><svg viewBox="0 0 24 24"><path d="m12 3.5 2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8L3.5 9.7l5.9-.9Z"/></svg></button>`
    host.append(card)
    mountWord(card.querySelector(".vprev"), v.p, { pad: 3 })
  }
}

function seg(id, options, current, onPick) {
  const host = document.getElementById(id)
  host.innerHTML = Object.entries(options)
    .map(([key, label]) => `<button type="button" data-v="${key}" aria-pressed="${String(key) === String(current)}">${label}</button>`)
    .join("")
  host.onclick = (event) => {
    const b = event.target.closest("button")
    if (!b) return
    onPick(b.dataset.v)
  }
}

function syncControls() {
  const p = state.p
  for (const [id, key] of [["c-rings", "rings"], ["c-step", "step"], ["c-line", "line"], ["c-gap", "gap"], ["c-track", "track"]]) {
    const input = document.getElementById(id)
    input.value = p[key]
    document.getElementById(`${id}-v`).textContent = String(p[key]).replace(".", ",")
  }
  document.getElementById("c-line").disabled = Boolean(p.fill)
  seg("c-scheme", Object.fromEntries(Object.entries(SCHEMES).map(([k, s]) => [k, s.name])), p.scheme, (v) => update({ scheme: v }))
  seg("c-weight", { 500: "500", 600: "600", 700: "700", 800: "800" }, p.weight, (v) => update({ weight: Number(v) }))
  seg("c-bg", { white: "Белый", land: "Бумага", dark: "Тёмный", blue: "Синий" }, p.bg, (v) => update({ bg: v }))
  seg("c-style", { line: "Линии", fill: "Заливка" }, p.fill ? "fill" : "line", (v) => update({ fill: v === "fill" }))
  seg("c-dash", { off: "Сплошное", on: "Пунктиром" }, p.dash ? "on" : "off", (v) => update({ dash: v === "on" }))
  seg("c-anim", ANIMS, state.anim, (v) => {
    state.anim = v
    renderHero()
  })
}

function update(patch) {
  state.p = { ...state.p, ...patch }
  renderHero()
}

for (const [id, key, num] of [["c-rings", "rings", true], ["c-step", "step"], ["c-line", "line"], ["c-gap", "gap"], ["c-track", "track"]]) {
  document.getElementById(id).addEventListener("input", (event) => {
    const value = Number(event.target.value)
    state.p = { ...state.p, [key]: num ? Math.round(value) : value }
    renderHero(false)
  })
  document.getElementById(id).addEventListener("change", () => animate(document.querySelector("#hero svg")))
}

document.getElementById("variants").addEventListener("click", (event) => {
  const card = event.target.closest(".vcard")
  if (!card) return
  const n = Number(card.dataset.n)
  if (event.target.closest(".star")) {
    state.favs = state.favs.includes(n) ? state.favs.filter((v) => v !== n) : [...state.favs, n]
    event.target.closest(".star").setAttribute("aria-pressed", String(state.favs.includes(n)))
    save()
    return
  }
  state.variant = n
  state.p = { ...VARIANTS.find((v) => v.n === n).p }
  document.querySelectorAll(".vcard").forEach((c) => c.classList.toggle("on", Number(c.dataset.n) === n))
  renderHero()
})

document.getElementById("replay").addEventListener("click", () => animate(document.querySelector("#hero svg")))
document.getElementById("hero").addEventListener("click", () => animate(document.querySelector("#hero svg")))
document.getElementById("reset").addEventListener("click", () => {
  const v = VARIANTS.find((item) => item.n === state.variant) ?? VARIANTS[1]
  state.p = { ...v.p }
  renderHero()
})
document.getElementById("copy").addEventListener("click", async () => {
  const text = `Изохроны, вариант ${state.variant}: ${summary(state.p)}, анимация «${ANIMS[state.anim]}»`
  const out = document.getElementById("copy-out")
  try {
    await navigator.clipboard.writeText(text)
    out.textContent = "Скопировано. Вставьте в чат."
  } catch {
    out.textContent = text
  }
})

document.fonts.ready.then(() => {
  renderVariants()
  renderHero()
})
