import { useState } from "react"
import { useWinterRoads, type WinterRoad } from "@/entities/reference"
import { useTranslation } from "@/shared/i18n"
import { Card, Checkbox, EmptyState, ErrorState, Select, Skeleton } from "@/shared/ui"
import { CalendarAxis, CalendarRow } from "./calendar-row"
import { calendarKey, calendarYears, routeRoad } from "./calendar-time"
import styles from "./winter-calendar.module.css"

function previousRoad(
  roads: readonly WinterRoad[],
  road: WinterRoad,
  year: number | undefined,
): WinterRoad | undefined {
  if (year === undefined) return undefined
  return roads.find((r) => calendarKey(r) === calendarKey(road) && r.season_end_year === year)
}

export function WinterCalendar() {
  const { t } = useTranslation()
  const query = useWinterRoads()
  const [chosen, setChosen] = useState<string | null>(null)
  const [compare, setCompare] = useState(false)
  const roads = (query.data ?? []).filter((road) =>
    routeRoad(road, [t("calendar:totalLabel"), t("calendar:aggregateLabel")]),
  )
  const years = calendarYears(roads)
  const year = Number(chosen ?? years[0])
  const previousYear = years.find((y) => y !== year)
  const rows = roads.filter((r) => r.season_end_year === year)
  const districts = [...new Set(rows.map((r) => r.district))]
  const seasonLabel = (end: number) =>
    t("calendar:year", { from: String(end - 1), to: String(end) })
  if (query.isError)
    return <ErrorState title={t("calendar:loadError")} onRetry={() => void query.refetch()} />
  if (!query.data) return <Skeleton lines={10} />
  if (!years.length) return <EmptyState icon="calendar" title={t("calendar:empty")} />
  return (
    <Card
      as="section"
      title={t("calendar:title")}
      description={t("calendar:routes", { count: rows.length })}
      actions={
        <div className={styles.controls}>
          <Select
            label={t("calendar:season")}
            value={String(year)}
            onChange={setChosen}
            options={years.map((y) => ({ value: String(y), label: seasonLabel(y) }))}
          />
          {previousYear ? (
            <Checkbox
              label={t("calendar:compare", {
                from: String(previousYear - 1),
                to: String(previousYear),
              })}
              checked={compare}
              onChange={setCompare}
            />
          ) : null}
        </div>
      }
    >
      <div className={styles.key}>
        <p>{t("calendar:hint")}</p>
        <div className={styles.swatches}>
          <span className={styles.swatch} data-kind="current">
            {t("calendar:currentBar", { year: seasonLabel(year) })}
          </span>
          {compare && previousYear ? (
            <span className={styles.swatch} data-kind="previous">
              {t("calendar:previousBar", { year: seasonLabel(previousYear) })}
            </span>
          ) : null}
        </div>
      </div>
      <div className={styles.schedule}>
        <CalendarAxis year={year} />
        {districts.map((district) => (
          <section key={district ?? "unknown"} aria-label={district ?? t("calendar:unknown")}>
            <p className={styles.district}>{district ?? t("calendar:unknown")}</p>
            {rows
              .filter((r) => r.district === district)
              .map((road) => (
                <CalendarRow
                  key={calendarKey(road)}
                  road={road}
                  year={year}
                  previous={compare ? previousRoad(roads, road, previousYear) : undefined}
                />
              ))}
          </section>
        ))}
      </div>
    </Card>
  )
}
