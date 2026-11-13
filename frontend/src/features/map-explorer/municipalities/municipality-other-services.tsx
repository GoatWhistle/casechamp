import { type MessageKey, useTranslation } from "@/shared/i18n"
import { type IconName, Stat } from "@/shared/ui"
import styles from "./municipality-index-card.module.css"
import {
  MunicipalityServiceHelp,
  MunicipalityServiceValue,
  type MunicipalNormative,
} from "./municipality-service-values"

const LABELS: Readonly<Record<string, MessageKey>> = {
  N03: "data:metric.normative_N03",
  N05: "data:metric.normative_N05",
  N06: "data:metric.normative_N06",
  N07: "data:metric.normative_N07",
  N08: "data:metric.normative_N08",
  N09: "data:metric.normative_N09",
}

const ICONS: Readonly<Record<string, IconName>> = {
  N03: "fire",
  N05: "office",
  N06: "employment",
  N07: "book",
  N08: "bus",
  N09: "bus",
}

export function MunicipalityOtherServices({
  rows,
}: {
  readonly rows: readonly MunicipalNormative[]
}) {
  const { t } = useTranslation()
  const available = rows.filter((row) => row.status === "available" && LABELS[row.criterion_id])
  if (!available.length) return null
  return (
    <section className={styles.rows} aria-label={t("map:municipalCard.otherServices")}>
      {available.map((row) => (
        <div key={row.criterion_id}>
          <Stat
            layout="row"
            icon={ICONS[row.criterion_id] ?? "building"}
            label={t(LABELS[row.criterion_id] ?? "map:municipalCard.otherServices")}
            value={<MunicipalityServiceValue row={row} />}
            help={
              <MunicipalityServiceHelp
                row={row}
                label={t(LABELS[row.criterion_id] ?? "map:municipalCard.otherServices")}
              />
            }
          />
        </div>
      ))}
    </section>
  )
}
