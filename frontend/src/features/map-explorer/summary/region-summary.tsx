import { useId } from "react"
import { type RegionSummary as RegionRow, type Season, useRegion } from "@/entities/region"
import { useNetworkMode } from "@/shared/hooks/use-network-mode"
import { useTranslation } from "@/shared/i18n"
import { Swap } from "@/shared/motion"
import { Banner, ButtonLink, Card, CloseButton, FactList, Skeleton } from "@/shared/ui"
import { MarketStanding } from "./market-standing"
import styles from "./region-summary.module.css"
import { useSummaryFacts } from "./summary-facts"
import { useReveal } from "./use-reveal"

export interface RegionSummaryProps {
  readonly id: string
  readonly season: Season
  readonly regions: readonly RegionRow[]
  readonly onClose?: (() => void) | undefined
}

function RegionPending() {
  return (
    <div className={styles.pending} aria-hidden="true">
      <Skeleton lines={2} />
      <Skeleton shape="block" />
      <Skeleton lines={2} />
    </div>
  )
}

export function RegionSummary({ id, season, regions, onClose }: RegionSummaryProps) {
  const { t } = useTranslation()
  const cardId = useId()
  const { networkMode } = useNetworkMode()
  const { data } = useRegion(id, season)
  const facts = useSummaryFacts({
    settlements: data?.settlements ?? 0,
    population: data?.population ?? 0,
    companies: data?.companies ?? null,
  })
  useReveal(cardId, data !== undefined, id)
  if (!data) return <RegionPending />
  const query = `season=${season}&network_mode=${networkMode}`
  return (
    <Card
      as="section"
      id={cardId}
      tabIndex={-1}
      title={
        <Swap swapKey={data.id} className={styles.name}>
          {data.name}
        </Swap>
      }
      actions={
        onClose ? <CloseButton label={t("map:selected.close")} onClick={onClose} /> : undefined
      }
      className={styles.region}
      data-stale={data.id !== id || undefined}
    >
      <Swap as="div" swapKey={data.id}>
        <FactList items={facts} label={t("map:facts.label")} />
      </Swap>
      <div className={styles.body}>
        <MarketStanding region={data} regions={regions} />
        <div className={styles.actions}>
          <ButtonLink to={`/regions/${data.id}?${query}`} icon="map">
            {t("map:selected.open")}
          </ButtonLink>
          <ButtonLink to={`/compare?ids=${data.id}&${query}`} variant="secondary" icon="compare">
            {t("map:selected.compare")}
          </ButtonLink>
        </div>
      </div>
    </Card>
  )
}

export interface OutsideRegionProps {
  readonly name: string
  readonly count: number
  readonly onClose?: (() => void) | undefined
}

export function OutsideRegion({ name, count, onClose }: OutsideRegionProps) {
  const { t } = useTranslation()
  return (
    <Card
      as="section"
      title={<span className={styles.name}>{name}</span>}
      actions={
        onClose ? <CloseButton label={t("map:selected.close")} onClick={onClose} /> : undefined
      }
      className={styles.region}
    >
      <div className={styles.body}>
        <Banner tone="info" title={t("map:selected.outsideModel", { name, count })} />
        <p className={styles.note}>{t("map:selected.outsideModelNote")}</p>
      </div>
    </Card>
  )
}
