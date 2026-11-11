import { useTranslation } from "@/shared/i18n"
import { Select, TextField } from "@/shared/ui"

export function AppraisalSource({
  source,
  basis,
  onSource,
  onBasis,
}: {
  readonly source: string
  readonly basis: "assumed" | "observed"
  readonly onSource: (value: string) => void
  readonly onBasis: (value: "assumed" | "observed") => void
}) {
  const { t } = useTranslation()
  return (
    <>
      <Select
        label={t("appraisal:basis")}
        value={basis}
        onChange={onBasis}
        options={[
          { value: "assumed", label: t("appraisal:assumed") },
          { value: "observed", label: t("appraisal:observed") },
        ]}
      />
      <TextField
        label={t("appraisal:source")}
        value={source}
        hint={t("appraisal:sourceHint")}
        onChange={(event) => onSource(event.target.value)}
      />
    </>
  )
}
