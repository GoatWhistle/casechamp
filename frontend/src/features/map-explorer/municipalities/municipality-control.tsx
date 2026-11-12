import type { useMunicipalities } from "@/entities/region"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Button, ButtonLink, HelpTip, Select, Skeleton, StatusBadge } from "@/shared/ui"
import styles from "./municipality-control.module.css"

export function MunicipalityControl({
  query,
  selected,
  onSelect,
}: {
  readonly query: ReturnType<typeof useMunicipalities>
  readonly selected: string | null
  readonly onSelect: (id: string) => void
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (query.isPending) return <Skeleton lines={1} />
  if (query.isError)
    return (
      <Button variant="secondary" icon="retry" onClick={() => void query.refetch()}>
        {t("map:municipalities.retry")}
      </Button>
    )
  if (!query.data.features.length)
    return (
      <p className={styles.notice} role="status">
        {t("map:municipalities.unavailable")}
      </p>
    )
  const current = query.data.features.find((feature) => feature.properties.id === selected)
  return (
    <div className={styles.control}>
      <Select
        label={t("map:municipalities.select")}
        hideLabel
        variant="floating"
        value={selected}
        onChange={onSelect}
        placeholder={t("map:municipalities.select")}
        options={query.data.features.map((feature) => ({
          value: feature.properties.id,
          label: feature.properties.name,
        }))}
      />
      <StatusBadge tone="warning" label={t("map:municipalities.partial")} />
      <HelpTip
        label={t("map:municipalities.help")}
        content={t("map:municipalities.basis", {
          date: query.data.metadata.observed_at
            ? f.date(query.data.metadata.observed_at)
            : t("map:municipalities.unknownDate"),
        })}
      />
      {current ? (
        <ButtonLink
          to={current.properties.source_url}
          reloadDocument
          variant="ghost"
          size="compact"
          icon="external"
        >
          {t("map:municipalities.source")}
        </ButtonLink>
      ) : null}
      <span className="visually-hidden" role="status">
        {current ? t("map:municipalities.selected", { name: current.properties.name }) : ""}
      </span>
    </div>
  )
}
