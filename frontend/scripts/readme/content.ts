import { readFileSync } from "node:fs"
import { join } from "node:path"

export type Tone = "accent" | "warning" | "neutral"

export interface ButtonSpec {
  readonly name: string
  readonly label: string
  readonly icon: "terminal" | "book-open" | "route"
  readonly href: string
  readonly primary: boolean
}

export interface BadgeSpec {
  readonly name: string
  readonly label?: string
  readonly value: string
  readonly href?: string
  readonly tone?: Tone
}

export interface BannerSpec {
  readonly promise: string
  readonly note: string
  readonly scale: string
  readonly low: string
  readonly high: string
}

export interface ReadmeContent {
  readonly banner: BannerSpec
  readonly buttons: readonly ButtonSpec[]
  readonly status: readonly BadgeSpec[]
  readonly stack: readonly BadgeSpec[]
  readonly nav: readonly BadgeSpec[]
}

export function readContent(repoRoot: string): ReadmeContent {
  return JSON.parse(
    readFileSync(join(repoRoot, "docs", "readme", "readme.json"), "utf8"),
  ) as ReadmeContent
}
