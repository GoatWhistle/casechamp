const NS = "http://www.w3.org/2000/svg"

const MODES = [
  { key: "air", label: "Авиация", plural: "авиарейсов", count: 480 },
  { key: "river", label: "Речные линии", plural: "речных линий", count: 266 },
  { key: "winter_road", label: "Зимники", plural: "зимников", count: 77 },
  { key: "ferry", label: "Паромы", plural: "паромов", count: 75 },
  { key: "ice_crossing", label: "Ледовые переправы", plural: "ледовых переправ", count: 71 },
  { key: "pontoon_bridge", label: "Понтонные мосты", plural: "понтонных мостов", count: 28 },
]

const VARIANTS = [
  { slug: "1-izohrony", name: "Изохроны" },
  { slug: "2-spletenie", name: "Сплетение" },
  { slug: "3-marshrut", name: "Маршрут" },
  { slug: "4-tablo", name: "Табло" },
]

const LUCIDE = {
  map: '<path d="M14.106 5.553a2 2 0 0 0 1.788 0l3.659-1.83A1 1 0 0 1 21 4.619v12.764a1 1 0 0 1-.553.894l-4.553 2.277a2 2 0 0 1-1.788 0l-4.212-2.106a2 2 0 0 0-1.788 0l-3.659 1.83A1 1 0 0 1 3 19.381V6.618a1 1 0 0 1 .553-.894l4.553-2.277a2 2 0 0 1 1.788 0z"/><path d="M15 5.764v15"/><path d="M9 3.236v15"/>',
  book: '<path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>',
  replay: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
  arrow: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
}

const reduced = matchMedia("(prefers-reduced-motion: reduce)")

function el(tag, attrs = {}, parent) {
  const node = document.createElementNS(NS, tag)
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v)
  if (parent) parent.appendChild(node)
  return node
}

function lucide(name, cls = "ico") {
  return `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${LUCIDE[name]}</svg>`
}

function modeIcon(key, cls = "ico") {
  const g = DATA.icons[key]
  const strokes = g.strokes.map((d) => `<path d="${d}"/>`).join("")
  const dots = g.dots.map(([x, y, r]) => `<circle class="dot" cx="${x}" cy="${y}" r="${r}"/>`).join("")
  return `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${strokes}${dots}</svg>`
}

function ease(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

function symbolSvg() {
  const s = DATA.symbol
  const rings = s.rings.map((d) => `<path class="mark-accent" fill-rule="evenodd" d="${d}"/>`)
  return `<svg viewBox="${s.viewBox}" aria-hidden="true">${rings.join("")}<path class="mark-base" fill-rule="evenodd" d="${s.word}"/></svg>`
}

function mountHeader() {
  const hdr = document.querySelector(".hdr")
  hdr.innerHTML = `
    <a class="hdr-brand" href="#" aria-label="Plexus, главная">${symbolSvg()}<span>plexus</span></a>
    <nav class="hdr-nav" aria-label="Разделы">
      <a href="#">Карта</a><a href="#">Регионы</a><a href="#">Сезоны</a><a href="#">Методика</a><a href="#">Источники</a>
    </nav>`
}

function mountReview(current, play) {
  const bar = document.createElement("nav")
  bar.className = "review"
  bar.setAttribute("aria-label", "Варианты главной")
  bar.innerHTML =
    VARIANTS.map(
      (v, i) =>
        `<a href="${v.slug}.html"${v.slug === current ? ' aria-current="page"' : ""}><span class="num">${i + 1}</span><span class="name">${v.name}</span></a>`,
    ).join("") + `<button type="button">${lucide("replay")}<span class="name">Повторить</span></button>`
  bar.querySelector("button").setAttribute("aria-label", "Повторить анимацию")
  bar.querySelector("button").addEventListener("click", play)
  document.body.prepend(bar)
}

function drawMap(svg, { ends = true } = {}) {
  const land = el("g", { class: "land" }, svg)
  for (const d of DATA.atlas.regions) el("path", { d }, land)
  const links = el("g", { class: "links" }, svg)
  const groups = {}
  const code = { a: "air", r: "river", w: "winter_road", i: "ice_crossing", f: "ferry", p: "pontoon_bridge" }
  const segs = {}
  const dots = {}
  for (const [m, x1, y1, x2, y2] of DATA.atlas.links) {
    const key = code[m]
    segs[key] = (segs[key] || "") + `M${x1} ${y1}L${x2} ${y2}`
    dots[key] = (dots[key] || "") + `M${x2} ${y2}h0`
  }
  for (const mode of MODES) {
    const g = el("g", { "data-mode": mode.key }, links)
    el("path", { class: "seg", d: segs[mode.key] || "" }, g)
    if (ends) el("path", { class: "end", d: dots[mode.key] || "" }, g)
    groups[mode.key] = g
  }
  return { land, links, groups }
}

function whenReady(fn) {
  const go = () => requestAnimationFrame(() => requestAnimationFrame(fn))
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(go)
  else go()
}

function cancelAll(root) {
  for (const a of root.getAnimations({ subtree: true })) a.cancel()
}

function mountIcons() {
  for (const n of document.querySelectorAll("[data-icon]")) {
    n.insertAdjacentHTML("afterbegin", lucide(n.dataset.icon))
  }
}
