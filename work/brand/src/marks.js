let uid = 0
const nextId = (p) => `${p}${(uid += 1)}`
const f1 = (n) => Math.round(n * 100) / 100
const poly = (pts) => `M${pts.map(([x, y]) => `${f1(x)} ${f1(y)}`).join("L")}`

function rng(seed) {
  let a = seed
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function saddle(small = false) {
  const id = nextId("sd")
  const R = 44
  const levels = small ? [0.32] : [0.08, 0.24, 0.46, 0.76]
  const steps = []
  for (let k = -1.25; k <= 1.2501; k += 0.05) steps.push(k)
  const parts = []
  levels.forEach((c, index) => {
    for (const sign of [1, -1]) {
      const valley = steps.map((v) => [50 + sign * Math.sqrt(v * v + c) * R, 50 + v * R])
      const ridge = steps.map((u) => [50 + u * R, 50 + sign * Math.sqrt(u * u + c) * R])
      parts.push(`<path class="ln tint" data-a="draw" data-o="${index}" d="${poly(valley)}"/>`)
      parts.push(`<path class="ln ink" data-a="draw" data-o="${index}" d="${poly(ridge)}"/>`)
    }
  })
  const w = small ? 4.2 : 2
  const d = R * Math.SQRT1_2
  return {
    vb: "0 0 100 100",
    body: `
      <defs><clipPath id="${id}"><circle cx="50" cy="50" r="${R}"/></clipPath></defs>
      <g clip-path="url(#${id})" style="--w:${w}">${parts.join("")}</g>
      <circle class="ln ink" style="--w:${small ? 5 : 2.6}" data-a="draw" data-o="0" cx="50" cy="50" r="${R}"/>
      <path class="ln acc" style="--w:${small ? 9 : 5.2}" data-a="draw" data-o="${levels.length}" d="M${50 - d} ${50 - d} ${50 + d} ${50 + d}M${50 + d} ${50 - d} ${50 - d} ${50 + d}"/>`,
  }
}

const TRANSIT = [
  { d: "M0 60V0h14a12 12 0 0 1 12 12v16a12 12 0 0 1-12 12H0", c: "air", st: [[0, 60]] },
  { d: "M40-20V40", c: "river", st: [[40, -20]] },
  { d: "M54 20h26v-8a12 12 0 0 0-12-12h-2a12 12 0 0 0-12 12v16a12 12 0 0 0 12 12h14", c: "ink", st: [[80, 40]] },
  { d: "M92 0l32 40", c: "acc", st: [] },
  { d: "M124 0 92 40", c: "ink", st: [] },
  { d: "M136 0v28a12 12 0 0 0 12 12h16V0", c: "winter", st: [[136, 0]] },
  { d: "M202 0h-16a10 10 0 0 0 0 20h6a10 10 0 0 1 0 20h-16", c: "ferry", st: [[202, 0], [176, 40]] },
]

function transit(mono = false) {
  const lines = TRANSIT.map((l, i) => `<path class="ln ${mono ? (l.c === "acc" ? "acc" : "ink") : l.c}" style="--w:8" data-a="draw" data-o="${i}" d="${l.d}"/>`)
  const stations = TRANSIT.flatMap((l) => l.st).map(([x, y]) => `<circle class="station" data-a="pop" data-o="7" cx="${x}" cy="${y}" r="5.4"/>`)
  return {
    vb: "-10 -30 222 100",
    body: `${lines.join("")}${stations.join("")}<circle class="station big" data-a="pop" data-o="8" cx="108" cy="20" r="8.5"/>`,
  }
}

function transitSmall() {
  return {
    vb: "84 -8 48 56",
    body: `<path class="ln ink" style="--w:9" data-a="draw" data-o="0" d="M124 0 92 40"/><path class="ln acc" style="--w:9" data-a="draw" data-o="1" d="M92 0l32 40"/><circle class="station big" style="--sw:4" data-a="pop" data-o="2" cx="108" cy="20" r="9"/>`,
  }
}

function weave(small = false) {
  const pos = small ? [34, 66] : [25, 50, 75]
  const w = small ? 15 : 10
  const gap = small ? 4.5 : 3.2
  const a = 12
  const b = 88
  const out = []
  pos.forEach((x, j) => {
    const cls = j === Math.floor(pos.length / 2) ? "acc" : "ink"
    out.push(`<g data-a="slideY" data-o="${j}"><path class="ln bgk flat" style="--w:${w + gap * 2}" d="M${x} ${a - gap}V${b + gap}"/><path class="ln ${cls} flat" style="--w:${w}" d="M${x} ${a}V${b}"/></g>`)
  })
  pos.forEach((y, i) => out.push(`<g data-a="slideX" data-o="${i + 1}"><path class="ln bgk flat" style="--w:${w + gap * 2}" d="M${a - gap} ${y}H${b + gap}"/><path class="ln ink flat" style="--w:${w}" d="M${a} ${y}H${b}"/></g>`))
  pos.forEach((y, i) =>
    pos.forEach((x, j) => {
      if ((i + j) % 2 === 1) return
      const cls = j === Math.floor(pos.length / 2) ? "acc" : "ink"
      const half = w / 2 + gap + 1
      out.push(`<path class="ln bgk flat" style="--w:${w + gap * 2}" data-a="fade" data-o="${pos.length + 1}" d="M${x} ${y - half}V${y + half}"/>`)
      out.push(`<path class="ln ${cls} flat" style="--w:${w}" data-a="fade" data-o="${pos.length + 1}" d="M${x} ${y - half - 0.5}V${y + half + 0.5}"/>`)
    }),
  )
  return { vb: "0 0 100 100", body: `<g transform="rotate(45 50 50) translate(50 50) scale(0.9) translate(-50 -50)">${out.join("")}</g>` }
}

function dots(small = false) {
  if (small) {
    const pts = [-1, -0.5, 0, 0.5, 1].flatMap((t) => (t === 0 ? [[50, 50]] : [[50 + t * 34, 50 + t * 34], [50 + t * 34, 50 - t * 34]]))
    return {
      vb: "0 0 100 100",
      body: pts.map(([x, y]) => `<circle class="${x === 50 ? "facc" : "fink"}" data-a="pop" data-o="${Math.round(Math.hypot(x - 50, y - 50) / 12)}" cx="${x}" cy="${y}" r="${x === 50 ? 12 : 8}"/>`).join(""),
    }
  }
  const rand = rng(20261108)
  const gauss = () => {
    let s = 0
    for (let i = 0; i < 6; i += 1) s += rand()
    return s / 6 - 0.5
  }
  const list = []
  for (let i = 0; i < 170; i += 1) {
    const diag = rand() < 0.5 ? 1 : -1
    const t = (rand() * 2 - 1) * (0.55 + 0.45 * rand())
    const spread = gauss() * (5 + Math.abs(t) * 7)
    const x = 50 + t * 42 + spread * Math.SQRT1_2
    const y = 50 + diag * t * 42 - diag * spread * Math.SQRT1_2
    const city = rand() < 0.045
    const r = city ? 3.3 + rand() * 1.6 : 0.7 + rand() ** 3 * 2.2
    list.push([x, y, r, city])
  }
  for (let i = 0; i < 26; i += 1) list.push([8 + rand() * 84, 8 + rand() * 84, 0.6 + rand() * 0.5, false, true])
  list.push([50, 50, 6.2, true])
  return {
    vb: "0 0 100 100",
    body: list
      .map(([x, y, r, city, bg]) => {
        const order = Math.round(Math.hypot(x - 50, y - 50) / 5)
        const cls = bg ? "ftint" : city ? "facc" : "fink"
        return `<circle class="${cls}" data-a="pop" data-o="${order}" data-step="45" cx="${f1(x)}" cy="${f1(y)}" r="${f1(r)}"/>`
      })
      .join(""),
  }
}

function fold(small = false) {
  const id = nextId("fd")
  const g = small ? 7 : 3.4
  return {
    vb: "0 0 100 100",
    body: `
      <defs><clipPath id="${id}"><rect x="7" y="7" width="86" height="86" rx="7"/></clipPath></defs>
      <g clip-path="url(#${id})">
        <path class="fink" data-a="unfold" data-o="0" d="M7 7h86L50 50Z"/>
        <path class="fdark" data-a="unfold" data-o="1" d="M93 7v86L50 50Z"/>
        <path class="fink" data-a="unfold" data-o="2" d="M93 93H7l43-43Z"/>
        <path class="facc" data-a="unfold" data-o="3" d="M7 93V7l43 43Z"/>
        <path class="ln bgk" style="--w:${g}" d="M7 7l86 86M93 7 7 93"/>
      </g>`,
  }
}

function stitch(small = false) {
  const n = small ? 5 : 7
  const cell = 92 / n
  const o = 4
  const inset = cell * 0.2
  const out = []
  if (!small) {
    for (let i = 0; i <= n; i += 1) for (let j = 0; j <= n; j += 1) out.push(`<circle class="ftint" cx="${f1(o + i * cell)}" cy="${f1(o + j * cell)}" r="0.7"/>`)
  }
  const cells = []
  for (let i = 0; i < n; i += 1) {
    cells.push([i, i, "ink"])
    if (i !== n - 1 - i) cells.push([i, n - 1 - i, "acc"])
  }
  const mid = (n - 1) / 2
  cells.forEach(([cx, cy, cls]) => {
    const x0 = o + cx * cell + inset
    const y0 = o + cy * cell + inset
    const x1 = o + (cx + 1) * cell - inset
    const y1 = o + (cy + 1) * cell - inset
    const order = Math.round(mid - Math.abs(cx - mid))
    const c = cx === mid && cy === mid ? "acc" : cls
    out.push(`<path class="ln ${c}" style="--w:${small ? 4.6 : 3}" data-a="draw" data-o="${order * 2}" d="M${f1(x0)} ${f1(y0)}L${f1(x1)} ${f1(y1)}"/>`)
    out.push(`<path class="ln ${c}" style="--w:${small ? 4.6 : 3}" data-a="draw" data-o="${order * 2 + 1}" d="M${f1(x1)} ${f1(y0)}L${f1(x0)} ${f1(y1)}"/>`)
  })
  return { vb: "0 0 100 100", body: out.join("") }
}

function lacing(small = false) {
  const ys = small ? [22, 50, 78] : [16, 33, 50, 67, 84]
  const L = 27
  const R = 73
  const out = [
    `<rect class="fink" data-a="slideL" data-o="0" x="${small ? 6 : 9}" y="6" width="${small ? 26 : 22}" height="88" rx="5"/>`,
    `<rect class="fink" data-a="slideR" data-o="0" x="${small ? 68 : 69}" y="6" width="${small ? 26 : 22}" height="88" rx="5"/>`,
  ]
  const w = small ? 6 : 4.4
  const segs = []
  segs.push([L, ys[0], R, ys[0], false])
  for (let i = 0; i < ys.length - 1; i += 1) {
    segs.push([L, ys[i], R, ys[i + 1], i % 2 === 0])
    segs.push([R, ys[i], L, ys[i + 1], i % 2 === 1])
  }
  segs.forEach(([x1, y1, x2, y2], k) => out.push(`<path class="ln acc" style="--w:${w}" data-a="draw" data-o="${k + 1}" d="M${x1} ${y1}L${x2} ${y2}"/>`))
  segs.forEach(([x1, y1, x2, y2, over], k) => {
    if (!over) return
    const mx = (x1 + x2) / 2
    const my = (y1 + y2) / 2
    const dx = (x2 - x1) * 0.16
    const dy = (y2 - y1) * 0.16
    out.push(`<path class="ln bgk" style="--w:${w + 4.4}" data-a="fade" data-o="${k + 1}" d="M${f1(mx - dx)} ${f1(my - dy)}L${f1(mx + dx)} ${f1(my + dy)}"/>`)
    out.push(`<path class="ln acc" style="--w:${w}" data-a="fade" data-o="${k + 1}" d="M${f1(mx - dx * 1.3)} ${f1(my - dy * 1.3)}L${f1(mx + dx * 1.3)} ${f1(my + dy * 1.3)}"/>`)
  })
  ys.forEach((y) => {
    out.push(`<circle class="eyelet" style="--sw:${small ? 3.4 : 2.4}" data-a="pop" data-o="${ys.length * 2}" cx="${L}" cy="${y}" r="${small ? 5.4 : 4.2}"/>`)
    out.push(`<circle class="eyelet" style="--sw:${small ? 3.4 : 2.4}" data-a="pop" data-o="${ys.length * 2}" cx="${R}" cy="${y}" r="${small ? 5.4 : 4.2}"/>`)
  })
  return { vb: "0 0 100 100", body: out.join("") }
}

function riverWord() {
  return {
    vb: "0 0 300 110",
    word: true,
    build(svg) {
      const text = svg.querySelector("text")
      const box = text.getBBox()
      const xs = [...text.textContent].map((_, i) => text.getStartPositionOfChar(i).x + text.getExtentOfChar(i).width / 2)
      const xc = xs[3]
      const yAt = (x) => 58 + Math.sin((x / box.width) * Math.PI * 2.2) * 5
      const pts = []
      for (let x = box.x - 10; x <= box.x + box.width + 10; x += 4) pts.push([x, yAt(x)])
      svg.querySelector(".river").setAttribute("d", poly(pts))
      const y = yAt(xc)
      svg.querySelector(".bridge").setAttribute("d", `M${f1(xc - 16)} ${f1(y)}H${f1(xc + 16)}`)
    },
    body: `
      <text class="wtext" x="10" y="80" font-size="84" font-weight="800" letter-spacing="-3">plexus</text>
      <path class="ln bgk river" style="--w:7" data-a="draw" data-o="1" d=""/>
      <path class="ln acc bridge" style="--w:6" data-a="draw" data-o="2" d=""/>`,
  }
}

function isoWord() {
  const layers = [
    [52, "t3"],
    [48, "bg"],
    [39, "t3"],
    [35, "bg"],
    [26, "t3"],
    [22, "bg"],
  ]
  return {
    vb: "0 -6 330 148",
    word: true,
    body: `${layers.map(([w, c], i) => `<text class="ring ${c}" data-a="ring" data-w="${w}" data-o="${layers.length - i}" x="38" y="90" font-size="76" font-weight="700" letter-spacing="-2" style="stroke-width:${w}">plexus</text>`).join("")}<text class="wtext knock" data-a="fade" data-o="0" x="38" y="90" font-size="76" font-weight="700" letter-spacing="-2">plexus</text>`,
  }
}

function threadWord() {
  return {
    vb: "0 0 300 110",
    word: true,
    build(svg) {
      const text = svg.querySelector("text")
      const n = text.textContent.length
      const pos = [...Array(n)].map((_, i) => {
        const p = text.getStartPositionOfChar(i).x
        const w = text.getExtentOfChar(i).width
        return [p, w]
      })
      const left = pos[0][0] - 18
      const right = pos[n - 1][0] + pos[n - 1][1] + 18
      const yMid = 62
      const yAt = (x) => yMid + Math.sin(((x - pos[0][0]) / (right - left)) * Math.PI * n) * 7
      const pts = []
      for (let x = left; x <= right; x += 3) pts.push([x, yAt(x)])
      svg.querySelector(".thread-under").setAttribute("d", poly(pts))
      const overs = pos
        .filter((_, i) => i % 2 === 0)
        .map(([p, w]) => {
          const seg = []
          for (let x = p - 2; x <= p + w + 2; x += 2) seg.push([x, yAt(x)])
          return poly(seg)
        })
        .join("")
      svg.querySelector(".thread-ko").setAttribute("d", overs)
      svg.querySelector(".thread-over").setAttribute("d", overs)
      svg.querySelector(".end-a").setAttribute("cx", f1(left))
      svg.querySelector(".end-a").setAttribute("cy", f1(yAt(left)))
      svg.querySelector(".end-b").setAttribute("cx", f1(right))
      svg.querySelector(".end-b").setAttribute("cy", f1(yAt(right)))
    },
    body: `
      <path class="ln acc thread-under" style="--w:4.4" data-a="draw" data-o="0" d=""/>
      <text class="wtext" x="22" y="82" font-size="84" font-weight="700" letter-spacing="-3">plexus</text>
      <path class="ln bgk thread-ko" style="--w:9" data-a="fade" data-o="1" d=""/>
      <path class="ln acc thread-over" style="--w:4.4" data-a="fade" data-o="1" d=""/>
      <circle class="facc end-a" data-a="pop" data-o="2" r="5"/>
      <circle class="facc end-b" data-a="pop" data-o="2" r="5"/>`,
  }
}

function xLetter(kind) {
  if (kind === "iso") {
    return {
      vb: "0 0 100 100",
      body: `${[[60, "t3"], [53, "bg"], [42, "t3"], [35, "bg"]].map(([w, c], i) => `<path class="ln ${c === "bg" ? "bgk" : c}" style="--w:${w}" data-a="ring" data-w="${w}" data-o="${3 - i}" d="M30 30 70 70M70 30 30 70"/>`).join("")}<path class="ln ink" style="--w:12" data-a="draw" data-o="4" d="M30 30 70 70M70 30 30 70"/>`,
    }
  }
  if (kind === "river") {
    return {
      vb: "0 0 100 100",
      body: `<path class="ln ink" style="--w:14" data-a="draw" data-o="0" d="M24 20 76 80M76 20 24 80"/><path class="ln bgk" style="--w:9" data-a="draw" data-o="1" d="M4 54c18-8 30 8 46 0s30-8 46 0"/><path class="ln acc" style="--w:8" data-a="draw" data-o="2" d="M36 51h28"/>`,
    }
  }
  return {
    vb: "0 0 100 100",
    body: `<path class="ln acc" style="--w:7" data-a="draw" data-o="0" d="M4 52c16-14 30 14 46 0s30-14 46 0"/><path class="ln ink" style="--w:14" data-a="draw" data-o="1" d="M26 22 74 78M74 22 26 78"/><path class="ln bgk" style="--w:13" data-a="fade" data-o="2" d="M38 46c4-4 8-4 12 0"/><path class="ln acc" style="--w:7" data-a="fade" data-o="2" d="M36 47.5c5-5 10-5 15 0"/>`,
  }
}

const CONCEPTS = [
  {
    n: 1,
    title: "Перевал",
    idea: "Горизонтали седловины, как на топографической карте. Нулевая горизонталь седла сама рисует X. Перевал это место, где дороги проходят через горы, то есть точка связи.",
    plus: "Настоящий картографический образ, его нельзя спутать с иконкой. Математически точная форма.",
    risk: "На 16 px остаются кольцо, X и одна пара горизонталей.",
    bg: "paper",
    mark: () => saddle(),
    small: () => saddle(true),
  },
  {
    n: 2,
    title: "Схема метро",
    idea: "Слово собрано как схема транспорта: каждая буква это линия своего вида транспорта, на концах станции, на x пересадка. Цвета взяты из палитры карты.",
    plus: "Самый узнаваемый вариант. Слово и знак одновременно, палитра связана с продуктом.",
    risk: "Пять цветов: для строгих документов нужна одноцветная версия, она показана ниже.",
    bg: "white",
    word: true,
    mark: () => transit(),
    alt: () => transit(true),
    small: () => transitSmall(),
  },
  {
    n: 3,
    title: "Ткань",
    idea: "Решётка из лент, которые по очереди проходят сверху и снизу. Plexus дословно значит «сплетение». Синяя лента держит всю ткань.",
    plus: "Плотный, весомый знак. Хорошо выглядит на мерче и в вышивке.",
    risk: "Плетение нужно рисовать точно, иначе лента читается как простая сетка.",
    bg: "land",
    mark: () => weave(),
    small: () => weave(true),
  },
  {
    n: 4,
    title: "Поселения",
    idea: "X из сотен точек разного размера: сёла вдоль двух дорог, крупные города синие. Похоже на карту плотности населения. Точки появляются от центра, как растёт доступ.",
    plus: "Сразу говорит о данных и о масштабе страны. Красивая анимация.",
    risk: "В малом размере точки заменяются на девять крупных.",
    bg: "ink",
    mark: () => dots(),
    small: () => dots(true),
  },
  {
    n: 5,
    title: "Сложенная карта",
    idea: "Лист карты, сложенный по двум диагоналям. X получается из пустоты между гранями. Одна грань синяя: часть территории, которую рассматриваем.",
    plus: "Негативное пространство: знак простой по форме, но с идеей. Отлично работает как иконка.",
    risk: "Похож на конверт, если убрать синюю грань.",
    bg: "white",
    mark: () => fold(),
    small: () => fold(true),
  },
  {
    n: 6,
    title: "Вышивка крестом",
    idea: "Большой X вышит маленькими крестиками по канве, как русская вышивка. Мы сшиваем территории. Стежки идут от краёв к центру.",
    plus: "Культурный слой, который поймёт жюри. Тёплый, человеческий образ для технического продукта.",
    risk: "Нужна аккуратная подача, иначе уйдёт в народный орнамент.",
    bg: "land",
    mark: () => stitch(),
    small: () => stitch(true),
  },
  {
    n: 7,
    title: "Шнуровка",
    idea: "Два берега стянуты шнуровкой. Шнур перекрещивается и проходит через люверсы. Связь буквально стягивает территории вместе.",
    plus: "Необычный и понятный образ. Анимация шнуровки сверху вниз запоминается.",
    risk: "Может напомнить обувь, если подать без контекста.",
    bg: "white",
    mark: () => lacing(),
    small: () => lacing(true),
  },
  {
    n: 8,
    title: "Река и мост",
    idea: "Слово перерезано рекой. Через реку переброшен синий мост ровно на букве x. Слово и есть знак: территория, разделённая и связанная.",
    plus: "История считывается за секунду. Работает без отдельного символа.",
    risk: "Шрифт должен быть очень жирным, чтобы река не съела буквы.",
    bg: "white",
    word: true,
    mark: () => riverWord(),
    small: () => xLetter("river"),
  },
  {
    n: 9,
    title: "Изохроны",
    idea: "Вокруг букв расходятся кольца, как изохроны вокруг города. Между близкими буквами кольца сливаются, как сливаются зоны доступности.",
    plus: "Самый «картографический» словесный знак. Кольца можно анимировать при загрузке.",
    risk: "Кольца требуют места вокруг слова.",
    bg: "white",
    word: true,
    mark: () => isoWord(),
    small: () => xLetter("iso"),
  },
  {
    n: 10,
    title: "Нить сквозь слово",
    idea: "Синяя нить проходит через слово, по очереди над буквами и под ними. Слово сплетено, как и написано.",
    plus: "Буквально показывает значение слова. Нить можно продолжить в интерфейсе как линию маршрута.",
    risk: "Нить тонкая: на маленьких размерах остаётся буква x с нитью.",
    bg: "paper",
    word: true,
    mark: () => threadWord(),
    small: () => xLetter("thread"),
  },
]
