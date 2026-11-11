import type { RegionSummary } from "@/entities/region"
import type { Formatters } from "@/shared/i18n"

export type CompareMetricLabel =
  | "compare:metrics.hansen"
  | "compare:metrics.coverage"
  | "compare:metrics.links"
  | "compare:metrics.population"
  | "compare:metrics.settlements"
  | "compare:metrics.companies"

export type CompareMetricHint =
  | "data:metricHint.hansen"
  | "data:metricHint.links"
  | "data:metricHint.population"
  | "data:metricHint.settlements"
  | "data:metricHint.companies"
  | "data:network.coverageHint"

export interface CompareMetric {
  readonly key: string
  readonly label: CompareMetricLabel
  readonly hint: CompareMetricHint
  readonly value: (region: RegionSummary) => number | null
  readonly format: (value: number, f: Formatters) => string
}

export const COMPARE_METRICS: readonly CompareMetric[] = [
  {
    key: "hansen",
    label: "compare:metrics.hansen",
    hint: "data:metricHint.hansen",
    value: (region) => region.hansen,
    format: (value, f) => f.number(value, 2),
  },
  {
    key: "coverage",
    label: "compare:metrics.coverage",
    hint: "data:network.coverageHint",
    value: (region) => region.index_population_coverage ?? null,
    format: (value, f) => f.percent(value, 1),
  },
  {
    key: "links",
    label: "compare:metrics.links",
    hint: "data:metricHint.links",
    value: (region) => region.links_season,
    format: (value, f) => f.integer(value),
  },
  {
    key: "population",
    label: "compare:metrics.population",
    hint: "data:metricHint.population",
    value: (region) => region.population,
    format: (value, f) => f.compact(value),
  },
  {
    key: "settlements",
    label: "compare:metrics.settlements",
    hint: "data:metricHint.settlements",
    value: (region) => region.settlements,
    format: (value, f) => f.integer(value),
  },
  {
    key: "companies",
    label: "compare:metrics.companies",
    hint: "data:metricHint.companies",
    value: (region) => region.companies,
    format: (value, f) => f.compact(value),
  },
]
