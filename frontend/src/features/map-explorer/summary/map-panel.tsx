import { memo } from "react"
import { ModeTotals, RegionLinks } from "@/entities/link"
import type { IndexStatus } from "@/entities/reference"
import {
  modelRegionId,
  type Overview,
  type RegionSummary,
  type Season,
  useRegion,
} from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { Banner, ScrollArea } from "@/shared/ui"
import type { MetricKey } from "../metric"
import { CountryOverview } from "./country-summary"
import styles from "./map-panel.module.css"
import { Ranking } from "./ranking"
import { OutsideRegion, RegionSummary as RegionCard } from "./region-summary"

export interface MapPanelProps {
  readonly overview: Overview
  readonly regions: readonly RegionSummary[]
  readonly metric: MetricKey
  readonly season: Season
  readonly selectedId: string | null
  readonly selectedName?: string | null | undefined
  readonly searchFor: (id: string) => string
  readonly onClear: () => void
}

function IndexBanner({ index }: { readonly index: IndexStatus }) {
  const { t } = useTranslation()
  if (index.status === "ready") return null
  return <Banner tone="info" title={t("map:index.missing")} />
}

interface CountryProps {
  readonly overview: Overview
  readonly regions: readonly RegionSummary[]
  readonly metric: MetricKey
  readonly searchFor: (id: string) => string
}

function Country({ overview, regions, metric, searchFor }: CountryProps) {
  return (
    <>
      <CountryOverview overview={overview} />
      <IndexBanner index={overview.index} />
      <Ranking regions={regions} metric={metric} searchFor={searchFor} className={styles.section} />
      <ModeTotals
        totals={overview.links_by_mode}
        total={overview.links}
        className={styles.section}
      />
    </>
  )
}

export const MapPanel = memo(function MapPanel({
  overview,
  regions,
  metric,
  season,
  selectedId: requestedId,
  selectedName,
  searchFor,
  onClear,
}: MapPanelProps) {
  const { t } = useTranslation()
  const selectedId = modelRegionId(requestedId, regions)
  const selected = useRegion(selectedId ?? "", season)
  return (
    <aside className={styles.panel}>
      <p className="visually-hidden" role="status">
        {selectedId && selected.data ? t("map:selectedStatus", { name: selected.data.name }) : ""}
      </p>
      <ScrollArea className={styles.scroll} label={t("map:overview.title")}>
        <div className={styles.content}>
          {selectedId ? (
            <>
              <RegionCard id={selectedId} season={season} regions={regions} onClose={onClear} />
              <RegionLinks
                key={selectedId}
                regionId={selectedId}
                season={season}
                className={styles.section}
              />
            </>
          ) : requestedId ? (
            <OutsideRegion
              name={selectedName ?? requestedId}
              count={regions.length}
              onClose={onClear}
            />
          ) : (
            <Country overview={overview} regions={regions} metric={metric} searchFor={searchFor} />
          )}
        </div>
      </ScrollArea>
    </aside>
  )
})
