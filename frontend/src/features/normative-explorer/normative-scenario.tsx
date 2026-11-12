import type { Assessment } from "@/entities/normative"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Banner, Card, FactList, NoValue } from "@/shared/ui"
import styles from "./normative-panel.module.css"

export function NormativeScenario({
  result,
}: {
  readonly result: Pick<Assessment, "comparison" | "closed_way_ids"> & {
    readonly ignored_way_ids?: number[]
  }
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  const comparison = result.comparison
  if (!comparison || result.closed_way_ids.length === 0) return null
  return (
    <Card as="div" title={t("normative:scenarioPhysical")} className={styles.result}>
      <FactList
        label={t("normative:scenarioPhysical")}
        items={[
          {
            key: "increased",
            label: t("normative:pathsIncreased"),
            value: f.integer(comparison.increased),
          },
          { key: "lost", label: t("normative:pathsLost"), value: f.integer(comparison.lost) },
          {
            key: "unchanged",
            label: t("normative:pathsUnchanged"),
            value: f.integer(comparison.unchanged),
          },
          {
            key: "unresolved",
            label: t("normative:pathsUnresolved"),
            value: f.integer(comparison.unresolved),
          },
        ]}
      />
      <p>
        {comparison.mean_change === null ? (
          <NoValue />
        ) : (
          t(comparison.unit === "metres" ? "normative:meanMetres" : "normative:meanMinutes", {
            value: f.number(comparison.mean_change, 1),
            count: f.integer(comparison.paired_paths),
          })
        )}
      </p>
      {comparison.decreased || comparison.restored ? (
        <p>
          {t("normative:pathsImproved", {
            count: f.integer(comparison.decreased + comparison.restored),
          })}
        </p>
      ) : null}
      {result.ignored_way_ids?.length ? (
        <Banner
          tone="warning"
          title={t("normative:ignoredRoads", { count: f.integer(result.ignored_way_ids.length) })}
          description={t("normative:ignoredRoadsNote")}
        />
      ) : null}
    </Card>
  )
}
