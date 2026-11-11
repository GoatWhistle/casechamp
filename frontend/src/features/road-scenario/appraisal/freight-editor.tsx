import { useTranslation } from "@/shared/i18n"
import { Button, TextField } from "@/shared/ui"
import { AppraisalNumber } from "./appraisal-number"
import { AppraisalSource } from "./appraisal-source"
import type { Freight } from "./appraisal-state"

const fields = [
  "trips_per_year",
  "before_hours",
  "after_hours",
  "before_km",
  "after_km",
  "rub_per_vehicle_hour",
  "rub_per_km",
] as const

export function FreightEditor({
  value,
  onChange,
  onRemove,
}: {
  readonly value: Freight
  readonly onChange: (value: Freight) => void
  readonly onRemove: () => void
}) {
  const { t } = useTranslation()
  return (
    <>
      <p>{t("appraisal:freightHint")}</p>
      <TextField
        label={t("appraisal:freightName")}
        value={value.name}
        onChange={(event) => onChange({ ...value, name: event.target.value })}
      />
      <TextField
        label={t("appraisal:freightOrigin")}
        value={value.origin_point_id ?? ""}
        onChange={(event) => onChange({ ...value, origin_point_id: event.target.value })}
      />
      <TextField
        label={t("appraisal:freightMarket")}
        value={value.market_city ?? ""}
        onChange={(event) => onChange({ ...value, market_city: event.target.value })}
      />
      <p>{t("appraisal:freightRouteHint")}</p>
      {fields
        .filter(
          (key) =>
            !(value.origin_point_id && value.market_city) ||
            !["before_hours", "after_hours", "before_km", "after_km"].includes(key),
        )
        .map((key) => (
          <AppraisalNumber
            key={key}
            label={t(`appraisal:freightFields.${key}`)}
            value={value[key] ?? Number.NaN}
            onChange={(number) => onChange({ ...value, [key]: number })}
          />
        ))}
      <AppraisalSource
        source={value.source}
        basis={value.basis ?? "assumed"}
        onSource={(source) => onChange({ ...value, source })}
        onBasis={(basis) => onChange({ ...value, basis })}
      />
      <Button icon="trash" variant="ghost" onClick={onRemove}>
        {t("appraisal:removeFlow")}
      </Button>
    </>
  )
}
