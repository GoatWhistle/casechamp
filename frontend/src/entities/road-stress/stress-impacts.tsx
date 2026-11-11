import type { StressImpact } from "@/shared/api/road-stress"
import { showStressView } from "@/shared/hooks/use-stress-view"
import { useTranslation } from "@/shared/i18n"
import { Button } from "@/shared/ui"
import styles from "./stress-card.module.css"
export function StressImpacts({
  id,
  rows,
  offset,
  setOffset,
  setOrigin,
}: {
  readonly id: string | null
  readonly rows: readonly StressImpact[]
  readonly offset: number
  readonly setOffset: (value: number) => void
  readonly setOrigin: (value: string) => void
}) {
  const { t } = useTranslation()
  const show = () => showStressView({ jobId: id, impacts: rows, route: null })
  return (
    <>
      <Button icon="map" variant="secondary" onClick={show} disabled={!rows.length}>
        {t("stress:show")}
      </Button>
      <ol className={styles.points}>
        {rows.map((r) => (
          <li key={r.point.id}>
            <strong>{r.point.name}</strong>
            <span>
              {t(r.external_isolation ? "stress:isolated" : "stress:delay", {
                minutes: Math.round(r.delay_minutes),
                markets: r.lost_markets,
              })}
            </span>
            <Button
              icon="map"
              variant="ghost"
              onClick={() => {
                setOrigin(r.point.id)
                showStressView({ jobId: id, impacts: [r], route: null, selected: r })
              }}
            >
              {t("stress:point")}
            </Button>
          </li>
        ))}
      </ol>
      <div className={styles.actions}>
        <Button
          icon="arrow-left"
          variant="ghost"
          disabled={offset === 0}
          onClick={() => setOffset(Math.max(0, offset - 10))}
        >
          {t("stress:previous")}
        </Button>
        <Button
          icon="chevron-right"
          variant="ghost"
          disabled={rows.length < 10}
          onClick={() => setOffset(offset + 10)}
        >
          {t("stress:next")}
        </Button>
      </div>
    </>
  )
}
