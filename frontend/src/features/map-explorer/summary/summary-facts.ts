import { useFormatters, useTranslation } from "@/shared/i18n"
import type { FactItem } from "@/shared/ui"

export interface SummaryCounts {
  readonly settlements: number
  readonly population: number
  readonly companies: number | null
}

const COMPACT_FROM = 1000
const MANY = 5

function nounCount(value: number): number {
  return value >= COMPACT_FROM ? MANY : value
}

export function useSummaryFacts({ settlements, population, companies }: SummaryCounts) {
  const { t } = useTranslation()
  const f = useFormatters()
  const items: FactItem[] = [
    {
      key: "settlements",
      value: f.integer(settlements),
      label: t("map:facts.settlements", { count: settlements }),
    },
    {
      key: "population",
      value: f.compact(population),
      label: t("map:facts.population", { count: nounCount(population) }),
    },
  ]
  if (companies !== null)
    items.push({
      key: "companies",
      value: f.compact(companies),
      label: t("map:facts.companies", { count: nounCount(companies) }),
    })
  return items
}
