import type { RegionDetail, RegionSummary } from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Swap } from "@/shared/motion"
import { Banner, Card, HelpTip, RankStrip } from "@/shared/ui"
import styles from "./market-standing.module.css"

export interface MarketStandingProps {
  readonly region: Pick<RegionDetail, "id" | "hansen" | "index_population_coverage">
  readonly regions: readonly RegionSummary[]
}

function medianOf(sorted: readonly number[]): number {
  const middle = Math.floor(sorted.length / 2)
  const upper = sorted[middle] ?? 0
  if (sorted.length % 2 === 1) return upper
  return ((sorted[middle - 1] ?? upper) + upper) / 2
}

export function MarketStanding({ region, regions }: MarketStandingProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const { hansen } = region
  if (hansen === null) return <Banner tone="info" title={t("map:index.missing")} />
  const values = regions
    .map((row) => row.hansen)
    .filter((value): value is number => value !== null)
    .sort((a, b) => a - b)
  const rank = 1 + values.filter((value) => value > hansen).length
  const total = Math.max(values.length, rank)
  const coverage = region.index_population_coverage
  return (
    <Card
      as="section"
      title={t("map:standing.title")}
      className={styles.standing}
      description={
        <Swap swapKey={region.id} className={styles.rank}>
          {t("map:standing.rank", { rank, total })}
        </Swap>
      }
      actions={<HelpTip content={t("data:metricHint.hansen")} label={t("common:ui.hint")} />}
    >
      <RankStrip
        values={values}
        current={hansen}
        label={t("map:standing.strip", { total })}
        currentLabel={<Swap swapKey={region.id}>{f.number(hansen, 2)}</Swap>}
        median={{
          value: medianOf(values),
          label: t("map:standing.median", { value: f.number(medianOf(values), 1) }),
        }}
        lowLabel={f.number(values[0] ?? hansen, 1)}
        highLabel={f.number(values.at(-1) ?? hansen, 1)}
      />
      {coverage === null || coverage === undefined ? null : (
        <p className={styles.coverage}>
          <Swap swapKey={region.id}>
            {t("data:network.coverage", { value: f.percent(coverage, 1) })}
          </Swap>
        </p>
      )}
    </Card>
  )
}
