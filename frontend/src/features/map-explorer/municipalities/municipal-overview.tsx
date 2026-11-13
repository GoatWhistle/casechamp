import { useMunicipalOverview } from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { Button, HelpTip, Skeleton } from "@/shared/ui"
import styles from "./municipal-overview.module.css"
import { MunicipalityCardFrame } from "./municipality-card-frame"

export function MunicipalOverview({
  regionId,
  onSelect,
  season,
  onClear,
}: {
  readonly regionId: string
  readonly season: "road" | "summer" | "winter"
  readonly onSelect: (id: string) => void
  readonly onClear: () => void
}) {
  const query = useMunicipalOverview(regionId, "", season)
  const { t } = useTranslation()
  return (
    <MunicipalityCardFrame name={t("map:municipalOverview.title")} onClear={onClear} foldOnPhone>
      <div className={styles.heading}>
        <span>{t("map:municipalOverview.connectivity")}</span>
        <HelpTip
          label={t("map:municipalOverview.orderHelp")}
          content={t("map:municipalOverview.connectivityHelp")}
        />
      </div>
      {query.isPending ? (
        <Skeleton lines={3} />
      ) : query.isError ? (
        <Button variant="secondary" icon="retry" onClick={() => void query.refetch()}>
          {t("map:municipalOverview.retry")}
        </Button>
      ) : (
        <div className={styles.content}>
          {query.data.region_connectivity.value !== null ? (
            <p className={styles.note}>
              {t("map:municipalOverview.reference", {
                value: query.data.region_connectivity.value,
              })}
            </p>
          ) : null}
          {!query.data.items.length ? <p>{t("map:municipalOverview.empty")}</p> : null}
          {query.data.items.slice(0, 3).map((item) => (
            <OverviewRow key={item.municipality_id} item={item} onSelect={onSelect} />
          ))}
        </div>
      )}
    </MunicipalityCardFrame>
  )
}

type OverviewItem = NonNullable<ReturnType<typeof useMunicipalOverview>["data"]>["items"][number]

function OverviewRow({
  item,
  onSelect,
}: {
  readonly item: OverviewItem
  readonly onSelect: (id: string) => void
}) {
  const { t } = useTranslation()
  const coverage = item.connectivity.population_coverage
  return (
    <div className={styles.item}>
      <Button
        variant="ghost"
        wrap
        className={styles.name}
        onClick={() => onSelect(item.municipality_id)}
      >
        {item.name}
      </Button>
      <span
        className={styles.value}
        data-problem={item.reasons.includes("below_region_connectivity") || undefined}
      >
        {item.connectivity.value === null
          ? t("map:municipalCard.unavailable")
          : t("map:municipalOverview.value", { value: item.connectivity.value })}
      </span>
      {coverage !== null && coverage < 1 ? (
        <p className={styles.note}>
          {t("map:municipalOverview.coverage", {
            value: (coverage ?? 0) * 100,
          })}
        </p>
      ) : null}
    </div>
  )
}
