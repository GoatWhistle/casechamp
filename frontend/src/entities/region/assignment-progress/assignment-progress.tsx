import type { components } from "@/shared/api/schema.gen"
import { useTranslation } from "@/shared/i18n"
import { HelpTip } from "@/shared/ui"

export function AssignmentProgress({
  value,
}: {
  readonly value: components["schemas"]["TrafficAssignmentProgress"] | null | undefined
}) {
  const { t } = useTranslation()
  if (!value) return null
  return (
    <p>
      {t("traffic:assignmentIteration", { iteration: value.iteration })}
      <HelpTip
        label={t("traffic:assignmentAccuracy")}
        content={t("traffic:assignmentGap", {
          gap: value.relative_gap * 100,
          target: (value.tolerance ?? 0.001) * 100,
        })}
      />
    </p>
  )
}
