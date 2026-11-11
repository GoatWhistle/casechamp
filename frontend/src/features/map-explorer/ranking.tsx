import { clsx } from "clsx"
import { type CSSProperties, useState } from "react"
import { Link } from "react-router"
import type { RegionSummary } from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Swap, staggerStyle } from "@/shared/motion"
import { Button, Card } from "@/shared/ui"
import { formatMetric, type MetricKey, metricValue } from "./metric"
import styles from "./ranking.module.css"

export interface RankingProps {
  readonly regions: readonly RegionSummary[]
  readonly metric: MetricKey
  readonly searchFor: (id: string) => string
  readonly className?: string | undefined
}

const LIMIT = 8

interface RankedRow {
  readonly region: RegionSummary
  readonly value: number
}

function rankRegions(regions: readonly RegionSummary[], metric: MetricKey): RankedRow[] {
  return regions
    .map((region) => ({ region, value: metricValue(region, metric) }))
    .filter((row): row is RankedRow => row.value !== null)
    .sort((a, b) => b.value - a.value)
}

export function Ranking({ regions, metric, searchFor, className }: RankingProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const [expanded, setExpanded] = useState(false)
  const [initialMetric] = useState(metric)
  const [moved, setMoved] = useState(false)
  if (!moved && metric !== initialMetric) setMoved(true)
  const ranked = rankRegions(regions, metric)
  const shown = expanded ? ranked : ranked.slice(0, LIMIT)
  const top = ranked[0]?.value ?? 1
  return (
    <Card
      as="section"
      title={<Swap swapKey={metric}>{t(`data:metric.${metric}`)}</Swap>}
      className={className}
    >
      <Swap as="div" swapKey={metric}>
        <ol className={styles.list}>
          {shown.map(({ region, value }, index) => (
            <li
              key={region.id}
              className={clsx(!moved && index < LIMIT && styles.enter)}
              style={staggerStyle(index)}
            >
              <Link
                to={{ search: searchFor(region.id) }}
                replace
                preventScrollReset
                state={{ reveal: true }}
                className={styles.row}
              >
                <span className={styles.place}>{f.integer(index + 1)}</span>
                <span className={styles.name}>{region.name}</span>
                <span className={styles.value}>{formatMetric(value, metric, f)}</span>
                <span
                  className={styles.bar}
                  style={{ "--v": top > 0 ? value / top : 0 } as CSSProperties}
                  aria-hidden="true"
                />
              </Link>
            </li>
          ))}
        </ol>
      </Swap>
      {shown.length < ranked.length ? (
        <Button
          variant="ghost"
          size="compact"
          icon="chevron-down"
          className={styles.more}
          onClick={() => setExpanded(true)}
        >
          {t("map:ranking.showAll", { count: ranked.length })}
        </Button>
      ) : null}
    </Card>
  )
}
