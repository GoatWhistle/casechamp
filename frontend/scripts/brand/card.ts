import type { ThemePalette } from "./marks.ts"
import type { CardText } from "./pages.ts"

export interface CardArt {
  readonly wordmark: string
  readonly map: string
  readonly ramp: readonly string[]
  readonly none: string
  readonly border: string
}

const escapeHtml = (text: string): string =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")

function mapStyle(art: CardArt): string {
  const steps = art.ramp.map((color, index) => `.map-step-${index + 1}{fill:${color}}`).join("")
  return `.map path{stroke:${art.border};stroke-width:0.8;stroke-linejoin:round}.map-step-0{fill:${art.none}}${steps}`
}

function sized(svg: string, className: string): string {
  return svg.replace("<svg", `<svg class="${className}" width="100%" height="100%"`)
}

export function socialCardHtml(
  art: CardArt,
  text: CardText,
  colors: ThemePalette,
  fonts: string,
  family: string,
): string {
  const ramp = art.ramp
    .map((color) => `<span style="flex:1;height:10px;background:${color}"></span>`)
    .join("")
  const body = `<div id="asset" style="position:relative;width:1200px;height:630px;overflow:hidden;background:${colors.surface};color:${colors.base};-webkit-font-smoothing:antialiased">
  <div style="position:absolute;left:566px;top:92px;width:740px;height:459px">${sized(art.map, "map")}</div>
  <div style="position:absolute;inset:64px auto 64px 80px;width:500px;display:grid;grid-template-rows:auto 1fr auto">
    <div style="width:236px;height:106px;margin-left:-18px">${sized(art.wordmark, "word")}</div>
    <div style="display:grid;align-content:center">
      <p style="font-size:68px;font-weight:700;line-height:1.02;letter-spacing:-0.035em;text-wrap:balance">${escapeHtml(text.tagline)}</p>
    </div>
    <div style="display:flex;gap:3px;width:280px;border-radius:5px;overflow:hidden">${ramp}</div>
  </div>
</div>`
  return `<!doctype html><html><head><meta charset="utf-8"><style>${fonts}*{box-sizing:border-box;margin:0;padding:0}body{background:transparent}#asset{font-family:${family}}${mapStyle(art)}</style></head><body>${body}</body></html>`
}
