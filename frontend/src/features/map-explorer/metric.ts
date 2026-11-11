import type { RegionSummary, Season } from "@/entities/region"
import type { Formatters } from "@/shared/i18n"
import type { IconName } from "@/shared/ui"

export type MetricKey = "hansen" | "links" | "population" | "companies" | "revenuePerCapita"

export const METRICS: readonly MetricKey[] = [
  "hansen",
  "links",
  "population",
  "companies",
  "revenuePerCapita",
]

export const METRIC_ICON = {
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
  if (metric === "hansen") return region.hansen
  if (metric === "links") return region.links_season
  if (metric === "population") return region.population
  if (metric === "companies") return region.companies
  if (region.revenue_rub === null || region.population <= 0) return null
  return region.revenue_rub / region.population
}

export function formatMetric(value: number, metric: MetricKey, f: Formatters): string {
  if (metric === "hansen") return f.number(value, Number.isInteger(value) ? 0 : 1)
  if (metric === "links") return f.integer(value)
  if (metric === "revenuePerCapita") return f.money(value, "RUB", 0)
  return f.compact(value)
}

export function formatThreshold(value: number, metric: MetricKey, f: Formatters): string {
  if (metric === "hansen") return f.number(value, Number.isInteger(value) ? 0 : 1)
  return metric === "links" ? f.integer(value) : f.compact(value)
}
