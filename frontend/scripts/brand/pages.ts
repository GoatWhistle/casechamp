import type { RasterAsset } from "./assets.ts"
import type { ThemePalette } from "./marks.ts"

export interface CardText {
  readonly name: string
  readonly tagline: string
  readonly description: string
  readonly site: string
}

const page = (body: string, fonts: string): string =>
  `<!doctype html><html><head><meta charset="utf-8"><style>${fonts}*{box-sizing:border-box;margin:0;padding:0}body{background:transparent}</style></head><body>${body}</body></html>`

export function tileHtml(
  mark: string,
  size: number,
  colors: ThemePalette,
  round: boolean,
  fill: number,
): string {
  const radius = round ? Math.round(size * 0.22) : 0
  const inner = Math.round(size * fill)
  return page(
    `<div id="asset" style="width:${size}px;height:${size}px;display:grid;place-items:center;background:${fill >= 1 ? "transparent" : colors.raised};border-radius:${radius}px"><div style="width:${inner}px;height:${inner}px">${mark}</div></div>`,
    "",
  )
}

export function rasterHtml(mark: string, asset: RasterAsset, colors: ThemePalette): string {
  const fill = 1
  return page(
    `<div id="asset" style="width:${asset.size}px;height:${asset.size}px;display:grid;place-items:center;background:${colors.accent}"><div style="width:${Math.round(asset.size * fill)}px;height:${Math.round(asset.size * fill)}px">${mark}</div></div>`,
    "",
  )
}
