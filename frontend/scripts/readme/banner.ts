import type { BannerSpec } from "./content.ts"
import { escapeHtml, type PageInput, shell } from "./page.ts"

const BANNER_STYLE = `
#asset.banner { display: grid; justify-items: center; align-content: center; gap: 20px; width: 880px; height: 200px; }
.word { width: 236px; }
.word svg { display: block; width: 100%; height: auto; overflow: visible; }
.promise { font-size: 22px; line-height: 1.3; text-align: center; }
.promise em { font-style: normal; }
`

export function bannerPage(input: PageInput, spec: BannerSpec): string {
  const t = input.theme
  const body = `<div id="asset" class="banner">
  <div class="word">${input.wordmark}</div>
  <p class="promise" style="color:${t.muted}">${escapeHtml(spec.promise)} <em style="color:${t.accent}">${escapeHtml(spec.accent)}</em></p>
</div>`
  return shell(input, body, BANNER_STYLE)
}

export function bannerAlt(spec: BannerSpec): string {
  return `Plexus. ${spec.promise} ${spec.accent}`
}
