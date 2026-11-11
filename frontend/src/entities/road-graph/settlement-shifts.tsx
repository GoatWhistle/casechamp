import { type CSSProperties, useMemo, useState } from "react"
import type { RoadJob } from "@/shared/api/road-graph"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { staggerStyle } from "@/shared/motion"
import { Button } from "@/shared/ui"
import { usePlaceNames } from "./road-jobs.queries"
import { deltaTone, signed } from "./scenario-summary"
import styles from "./settlement-shifts.module.css"

type Effect = NonNullable<NonNullable<RoadJob["result"]>["settlement_effects"]>[number]

export interface SettlementShiftsProps {
  readonly effects: readonly Effect[]
  readonly limit: number
  readonly expandable: boolean
}

export function SettlementShifts({ effects, limit, expandable }: SettlementShiftsProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const [open, setOpen] = useState(false)
  const sorted = useMemo(
    () => [...effects].sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)),
    [effects],
  )
  const shown = open ? sorted : sorted.slice(0, limit)
  const names = usePlaceNames((expandable ? sorted : shown).map((effect) => effect.point_id))
  if (!sorted.length) return null
  const peak = Math.max(...sorted.map((effect) => Math.abs(effect.delta))) || 1
  return (
    <div className={styles.shifts}>
      <p className={styles.heading}>{t("graph:outcome.top")}</p>
      <ul className={styles.list}>
        {shown.map((effect, index) => (
          <li
            key={effect.point_id}
            className={styles.row}
            data-tone={deltaTone(effect.delta)}
            style={
              {
                ...staggerStyle(index),
                "--ratio": Math.max(Math.abs(effect.delta) / peak, 0.02),
              } as CSSProperties
            }
          >
            <span className={styles.place}>{names.get(effect.point_id) ?? effect.point_id}</span>
            <span className={styles.value}>{signed(effect.delta, f.number)}</span>
            <span className={styles.bar} aria-hidden="true" />
          </li>
        ))}
      </ul>
      {expandable && sorted.length > limit ? (
        <Button
          variant="ghost"
          size="compact"
          icon={open ? "minus" : "chevron-down"}
          className={styles.more}
          onClick={() => setOpen(!open)}
        >
          {open ? t("graph:outcome.fewer") : t("graph:outcome.more", { count: sorted.length })}
        </Button>
      ) : null}
    </div>
  )
}
