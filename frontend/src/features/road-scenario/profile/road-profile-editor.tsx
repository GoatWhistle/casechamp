import { useTranslation } from "@/shared/i18n"
import { NumberField, Select } from "@/shared/ui"

export interface RoadProfileState {
  readonly lanes: string
  readonly action: "lanes" | "closure" | "opening"
}

export function RoadProfileEditor({
  value,
  onChange,
}: {
  readonly value: RoadProfileState
  readonly onChange: (value: RoadProfileState) => void
}) {
  const { t } = useTranslation()
  const lanes = Number(value.lanes.replace(",", "."))
  const invalid = value.lanes.trim() !== "" && (!Number.isInteger(lanes) || lanes < 1 || lanes > 32)
  return (
    <>
      <Select
        label={t("graph:profile.action")}
        value={value.action}
        onChange={(action) => onChange({ ...value, action })}
        options={[
          { value: "lanes", label: t("graph:profile.edit") },
          { value: "closure", label: t("traffic:kind.closure") },
          { value: "opening", label: t("traffic:kind.opening") },
        ]}
      />
      {value.action === "lanes" ? (
        <NumberField
          label={t("graph:profile.lanes")}
          value={value.lanes}
          error={invalid ? t("graph:profile.lanesError") : undefined}
          onChange={(event) => onChange({ ...value, lanes: event.target.value })}
        />
      ) : null}
      <p>{t("graph:profile.hint")}</p>
    </>
  )
}
