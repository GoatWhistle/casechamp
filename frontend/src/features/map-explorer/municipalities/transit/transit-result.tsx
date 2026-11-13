import type { components } from "@/shared/api/schema.gen"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { HelpTip, Stat } from "@/shared/ui"
import styles from "./transit-result.module.css"

type Plan = components["schemas"]["TransitPlanResponse"]

export function TransitResult({ data }: { readonly data: Plan }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const journey = data.result.journey
  const duration = (seconds: number) =>
    t("map:transit.minutes", { value: f.number(seconds / 60, 1) })
  const help = t("map:transit.help", {
    date: data.coverage.source_date,
    walk: data.result.maximum_walk_metres,
    transfer: data.result.transfer_seconds / 60,
    located: data.coverage.located_stops,
    total: data.coverage.stops.length,
    transfers: Math.max(0, (journey?.boardings ?? 0) - 1),
  })
  if (!journey)
    return (
      <p className={styles.empty}>
        {t("map:transit.notFound")} <HelpTip label={t("map:transit.details")} content={help} />
      </p>
    )
  const totals = journey.legs.reduce(
    (values, leg) => {
      const mode = leg.mode === "dwell" ? "bus" : leg.mode
      values[mode] += leg.arrival - leg.departure
      return values
    },
    { walk: 0, wait: 0, bus: 0 },
  )
  return (
    <div className={styles.content} aria-live="polite">
      <Stat
        layout="row"
        label={t("map:transit.total")}
        value={duration(journey.arrival - journey.departure)}
        help={<HelpTip label={t("map:transit.details")} content={help} />}
      />
      <span className={styles.arrival}>
        {t(
          Math.ceil(journey.arrival / 60) >= 1440
            ? "map:transit.arrivalLater"
            : "map:transit.arrival",
          {
            time: sourceClock(journey.arrival),
            day: Math.floor(Math.ceil(journey.arrival / 60) / 1440),
          },
        )}
      </span>
      {totals.walk > 0 ? (
        <Stat
          layout="row"
          icon="route"
          label={t("map:transit.walk")}
          value={duration(totals.walk)}
        />
      ) : null}
      {totals.wait > 0 ? (
        <Stat
          layout="row"
          icon="clock"
          label={t("map:transit.wait")}
          value={duration(totals.wait)}
        />
      ) : null}
      {totals.bus > 0 ? (
        <Stat layout="row" icon="bus" label={t("map:transit.bus")} value={duration(totals.bus)} />
      ) : null}
    </div>
  )
}

function sourceClock(seconds: number): string {
  const minutes = Math.ceil(seconds / 60) % 1440
  return `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`
}
