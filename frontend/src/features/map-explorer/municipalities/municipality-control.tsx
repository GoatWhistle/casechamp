import type { useMunicipalities } from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { Button, Select, Skeleton } from "@/shared/ui"
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
  if (query.isPending) return <Skeleton lines={1} />
  if (query.isError)
    return (
      <Button variant="secondary" icon="retry" onClick={() => void query.refetch()}>
        {t("map:municipalities.retry")}
      </Button>
    )
  if (!query.data.features.length) return null
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
      <span className="visually-hidden" role="status">
        {current ? t("map:municipalities.selected", { name: current.properties.name }) : ""}
      </span>
    </div>
  )
}
