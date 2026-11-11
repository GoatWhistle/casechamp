import { useEffect, useState } from "react"
import { useTranslation } from "@/shared/i18n"
import { NumberField } from "@/shared/ui"

export function AppraisalNumber({
  label,
  value,
  onChange,
}: {
  readonly label: string
  readonly value: number
  readonly onChange: (value: number) => void
}) {
  const { t } = useTranslation()
  const [raw, setRaw] = useState(Number.isNaN(value) ? "" : String(value))
  useEffect(() => {
    setRaw(Number.isNaN(value) ? "" : String(value))
  }, [value])
  return (
    <NumberField
      label={label}
      value={raw}
      error={Number.isFinite(value) && value < 0 ? t("appraisal:nonnegative") : undefined}
      onChange={(event) => {
        setRaw(event.target.value)
        const text = event.target.value.trim().replace(",", ".")
        onChange(text ? Number(text) : Number.NaN)
      }}
    />
  )
}
