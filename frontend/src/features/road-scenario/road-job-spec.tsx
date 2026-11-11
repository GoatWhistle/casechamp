import { LinkChanges, scenarioParts } from "@/entities/road-graph"
import type { RoadJob } from "@/shared/api/road-graph"
import { useFormatters, useTranslation } from "@/shared/i18n"
import styles from "./road-scenario.module.css"

export function RoadJobSpec({
  job,
  names = [],
}: {
  readonly job: RoadJob
  readonly names?: readonly string[]
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <ul className={styles.spec} aria-label={t("graph:result.spec")}>
      {scenarioParts(job).map((part) => (
        <li key={part.id} className={styles.specItem}>
          <div>
            {t(part.text, part.values)}
            {part.id === "roads" && names.length ? (
              <span className={styles.specDetail}>{f.list(names)}</span>
            ) : null}
            {part.id === "links" ? (
              <LinkChanges links={job.links} className={styles.specDetail} />
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  )
}
