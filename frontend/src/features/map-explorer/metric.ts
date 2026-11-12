import type { RegionSummary, Season } from "@/entities/region"
import type { Formatters } from "@/shared/i18n"
import type { IconName } from "@/shared/ui"

export type BaseMetricKey = "hansen" | "links" | "population" | "companies" | "revenuePerCapita"
export type NormativeId = "N01" | "N02" | "N03" | "N04" | "N05" | "N06" | "N07" | "N08" | "N09"
export type MetricKey = BaseMetricKey | `normative_${NormativeId}`

export function normativeId(metric: MetricKey): NormativeId | null {
  return metric.startsWith("normative_") ? (metric.slice(10) as NormativeId) : null
}

export const METRICS: readonly MetricKey[] = [
  "hansen",
  "links",
  "population",
  "companies",
  "revenuePerCapita",
  "normative_N01",
  "normative_N02",
  "normative_N03",
  "normative_N04",
  "normative_N05",
  "normative_N06",
  "normative_N07",
  "normative_N08",
  "normative_N09",
]

export const METRIC_ICON = {
  normative_N01: "hospital",
  normative_N02: "hospital",
  normative_N03: "fire",
  normative_N04: "school",
  normative_N05: "office",
  normative_N06: "employment",
  normative_N07: "book",
  normative_N08: "bus",
  normative_N09: "bus",
  hansen: "route",
  links: "link",
  population: "users",
  companies: "building",
  revenuePerCapita: "money",
} as const satisfies Record<MetricKey, IconName>

export const SEASONS: readonly Season[] = ["all", "summer", "winter"]

export const DEFAULT_METRIC: MetricKey = "hansen"

export const DEFAULT_SEASON: Season = "all"

export function isMetricKey(value: string | null): value is MetricKey {
  return METRICS.some((metric) => metric === value)
}

export function isSeason(value: string | null): value is Season {
  return SEASONS.some((season) => season === value)
}

export function dependsOnSeason(metric: MetricKey): boolean {
  return metric === "links" || metric === "hansen"
}

export function metricValue(region: RegionSummary, metric: MetricKey): number | null {
  if (normativeId(metric)) return null
  if (metric === "hansen") return region.hansen
  if (metric === "links") return region.links_season
  if (metric === "population") return region.population
  if (metric === "companies") return region.companies
  if (region.revenue_rub === null || region.population <= 0) return null
  return region.revenue_rub / region.population
}

export function formatMetric(value: number, metric: MetricKey, f: Formatters): string {
  if (normativeId(metric)) return f.percent(value / 100, 1)
  if (metric === "hansen") return f.number(value, Number.isInteger(value) ? 0 : 1)
  if (metric === "links") return f.integer(value)
  if (metric === "revenuePerCapita") return f.money(value, "RUB", 0)
  return f.compact(value)
}

export function formatThreshold(value: number, metric: MetricKey, f: Formatters): string {
  if (normativeId(metric)) return f.percent(value / 100, 0)
  if (metric === "hansen") return f.number(value, Number.isInteger(value) ? 0 : 1)
  return metric === "links" ? f.integer(value) : f.compact(value)
}
