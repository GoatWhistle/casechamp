import { useMemo, useState } from "react"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Card, EmptyState, ErrorState, Skeleton } from "@/shared/ui"
import { type Link, type Mode, useRegionLinks } from "../link.queries"
import { groupByMode, type LinkTally, tallyLinks } from "../link-modes"
import { ModeBar } from "../mode-bar/mode-bar"
import { ModeSwatch } from "../mode-swatch/mode-swatch"
import { ModeGroup } from "./mode-group"
import styles from "./region-links.module.css"

type Season = NonNullable<Link["season"]>

export interface RegionLinksProps {
  readonly regionId: string
  readonly season: Season
  readonly className?: string | undefined
}

interface LinkKeyProps {
  readonly tally: LinkTally
  readonly season: Season
}

function LinkKey({ tally, season }: LinkKeyProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const seasonal = season !== "all" && tally.unknownSeason > 0
  if (tally.model === 0 && !seasonal) return null
  return (
    <div className={styles.key}>
      {tally.model > 0 ? (
        <p className={styles.keyRow}>
          <span className={styles.keyItem}>
            <ModeSwatch mode={null} />
            {t("links:sourced")}
            <b>{f.integer(tally.total - tally.model)}</b>
          </span>
          <span className={styles.keyItem}>
            <ModeSwatch mode={null} model />
            {t("links:modelled")}
            <b>{f.integer(tally.model)}</b>
          </span>
        </p>
      ) : null}
      {seasonal ? (
        <p className={styles.keyRow}>
          <span className={styles.keyItem}>
            {t(`links:inSeason.${season}`)}
            <b>{f.integer(tally.total - tally.unknownSeason)}</b>
          </span>
          <span className={styles.keyItem}>
            {t("data:season.unknown")}
            <b>{f.integer(tally.unknownSeason)}</b>
          </span>
        </p>
      ) : null}
    </div>
  )
}

function LinksBody({
  links,
  season,
}: {
  readonly links: readonly Link[]
  readonly season: Season
}) {
  const { t } = useTranslation()
  const [active, setActive] = useState<Mode | null>(null)
  const tally = useMemo(() => tallyLinks(links), [links])
  const groups = useMemo(() => groupByMode(links), [links])
  return (
    <>
      <div className={styles.chart}>
        <ModeBar rows={tally.shares} active={active} />
        <LinkKey tally={tally} season={season} />
      </div>
      <ul className={styles.groups} aria-label={t("links:groups")}>
        {tally.shares.map((share) => (
          <ModeGroup
            key={share.mode}
            share={share}
            links={groups.get(share.mode) ?? []}
            defaultOpen={tally.shares.length === 1}
            onActive={setActive}
          />
        ))}
      </ul>
    </>
  )
}

export function RegionLinks({ regionId, season, className }: RegionLinksProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const links = useRegionLinks(regionId, season)
  const data = links.isPlaceholderData ? undefined : links.data
  return (
    <Card
      as="section"
      title={t("data:metric.links")}
      className={className}
      actions={
        data === undefined ? undefined : (
          <span className={styles.total}>{f.integer(data.length)}</span>
        )
      }
    >
      {links.isError ? (
        <ErrorState title={t("errors:kind.server")} onRetry={() => void links.refetch()} />
      ) : data === undefined ? (
        <Skeleton lines={5} />
      ) : data.length > 0 ? (
        <LinksBody links={data} season={season} />
      ) : (
        <EmptyState icon="link" title={t("links:empty")} />
      )}
    </Card>
  )
}
