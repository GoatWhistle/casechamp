import type { BannerSpec } from "./content.ts"
import { escapeHtml, type PageInput, shell } from "./page.ts"

function mapStyle(input: PageInput): string {
  const t = input.theme
  const steps = t.ramp.map((color, index) => `.map .map-step-${index + 1}{fill:${color}}`).join("")
  return `.map path{stroke:${t.mapBorder};stroke-width:0.9;stroke-linejoin:round}.map .map-step-0{fill:${t.mapNone}}${steps}`
}

const BANNER_STYLE = `
#asset.banner { display: grid; grid-template-columns: 344px 1fr; align-items: center; gap: 16px; width: 880px; padding: 20px 0 16px; }
.lede { display: grid; gap: 18px; justify-items: start; }
.word { width: 188px; margin-bottom: 2px; }
.word svg, .map svg { display: block; width: 100%; height: auto; overflow: visible; }
.promise { font-size: 29px; font-weight: 700; line-height: 1.12; letter-spacing: -0.03em; text-wrap: balance; }
.note { font-size: 15px; line-height: 1.45; text-wrap: pretty; }
.scale { display: grid; gap: 7px; width: 260px; margin-top: 4px; }
.ramp { display: flex; gap: 3px; height: 8px; border-radius: 4px; overflow: hidden; }
.ramp span { flex: 1; }
.ends { display: flex; justify-content: space-between; font-size: 12px; font-weight: 500; }
.map { margin-right: -8px; }
`

export function bannerPage(input: PageInput, spec: BannerSpec): string {
  const t = input.theme
  const ramp = t.ramp.map((color) => `<span style="background:${color}"></span>`).join("")
  const body = `<div id="asset" class="banner">
  <div class="lede">
    <div class="word">${input.wordmark}</div>
    <p class="promise">${escapeHtml(spec.promise)}</p>
    <p class="note" style="color:${t.muted}">${escapeHtml(spec.note)}</p>
    <div class="scale">
      <div class="ramp">${ramp}</div>
      <div class="ends" style="color:${t.muted}"><span>${escapeHtml(spec.low)}</span><span>${escapeHtml(spec.scale)}</span><span>${escapeHtml(spec.high)}</span></div>
    </div>
  </div>
  <div class="map">${input.map}</div>
</div>`
  return shell(input, body, `${BANNER_STYLE}${mapStyle(input)}`)
}
