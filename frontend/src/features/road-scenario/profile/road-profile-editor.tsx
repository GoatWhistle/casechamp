import { useTranslation } from "@/shared/i18n"
import { NumberField, Select, TextField } from "@/shared/ui"

export interface RoadProfileState {
  readonly lanes: string
  readonly highway: string
  readonly surface: string
  readonly speed: string
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
  const speed = Number(value.speed.replace(",", "."))
  const invalidLanes =
    value.lanes.trim() !== "" && (!Number.isInteger(lanes) || lanes < 1 || lanes > 32)
  const invalidSpeed =
    value.speed.trim() !== "" && (!Number.isFinite(speed) || speed <= 0 || speed > 200)
  return (
    <>
      <NumberField
        label={t("graph:profile.lanes")}
        value={value.lanes}
        error={invalidLanes ? t("graph:profile.lanesError") : undefined}
        onChange={(event) => onChange({ ...value, lanes: event.target.value })}
      />
      <Select
        label={t("graph:profile.highway")}
        value={value.highway}
        onChange={(highway) => onChange({ ...value, highway })}
        options={[
          { value: "", label: t("graph:profile.keep") },
          { value: "motorway", label: t("graph:profile.motorway") },
          { value: "trunk", label: t("graph:profile.trunk") },
          { value: "primary", label: t("graph:profile.primary") },
          { value: "secondary", label: t("graph:profile.secondary") },
          { value: "tertiary", label: t("graph:profile.tertiary") },
          { value: "residential", label: t("graph:profile.residential") },
          { value: "track", label: t("graph:profile.track") },
        ]}
      />
      <Select
        label={t("graph:profile.surface")}
        value={value.surface}
        onChange={(surface) => onChange({ ...value, surface })}
        options={[
          { value: "", label: t("graph:profile.keep") },
          { value: "asphalt", label: t("graph:profile.asphalt") },
          { value: "concrete", label: t("graph:profile.concrete") },
          { value: "gravel", label: t("graph:profile.gravel") },
          { value: "ground", label: t("graph:profile.ground") },
        ]}
      />
      <NumberField
        label={t("graph:profile.speed")}
        value={value.speed}
        error={invalidSpeed ? t("graph:profile.speedError") : undefined}
        onChange={(event) => onChange({ ...value, speed: event.target.value })}
      />
      <p>{t("graph:profile.hint")}</p>
    </>
  )
}

export function RoadParameterEditor({
  mode,
  value,
  onChange,
  factor,
  onFactor,
}: {
  readonly mode: "profile" | "speed"
  readonly value: RoadProfileState
  readonly onChange: (value: RoadProfileState) => void
  readonly factor: string
  readonly onFactor: (value: string) => void
}) {
  const { t } = useTranslation()
  const speed = Number(factor.replace(",", "."))
  const valid = factor.trim() !== "" && Number.isFinite(speed) && speed >= 0 && speed <= 3
  return mode === "profile" ? (
    <RoadProfileEditor value={value} onChange={onChange} />
  ) : (
    <TextField
      label={t("graph:factor")}
      value={factor}
      onChange={(event) => onFactor(event.target.value)}
      inputMode="decimal"
      hint={t("graph:factorHint")}
      error={valid ? undefined : t("graph:factorError")}
    />
  )
}
