import type { CSSProperties } from "react"
import type { WinterRoad } from "@/entities/reference"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Disclosure, Icon, NoValue } from "@/shared/ui"
import styles from "./calendar-row.module.css"
import { calendarMonths, calendarPosition } from "./calendar-time"

interface CalendarRowProps {
  readonly road: WinterRoad
  readonly previous: WinterRoad | undefined
  readonly year: number
}

const STOP_SEPARATOR = /\s+-\s+/

function tickStyle(at: number): CSSProperties {
  return { "--tick-left": `${at}%` } as CSSProperties
}

export function CalendarAxis({ year }: { readonly year: number }) {
  const { t } = useTranslation()
  return (
    <div className={styles.axis}>
      <span className={styles.axisLabel}>{t("seasons:route")}</span>
      <div className={styles.months}>
        {calendarMonths(year).map((m) => (
          <span key={m.key} className={styles.month} style={tickStyle(m.at)}>
            <span className={styles.monthLong}>{m.label}</span>
            <span className={styles.monthShort}>{m.short}</span>
          </span>
        ))}
      </div>
      <span className={styles.axisLabel}>{t("calendar:dates")}</span>
    </div>
  )
}

function RouteName({ route }: { readonly route: string }) {
  let offset = 0
  const stops = route.split(STOP_SEPARATOR).map((stop) => {
    const start = offset
    offset += stop.length + 1
    return { stop, start }
  })
  return (
    <strong className={styles.route}>
      {stops.map(({ stop, start }) => (
        <span key={start} className={styles.stop}>
          {start > 0 ? <Icon name="arrow-right" size="sm" className={styles.arrow} /> : null}
          {stop}
        </span>
      ))}
    </strong>
  )
}

function Bar({
  road,
  year,
  previous = false,
}: {
  readonly road: WinterRoad | undefined
  readonly year: number
  readonly previous?: boolean
}) {
  if (!road?.opening_date || !(road.closure_date ?? road.report_date)) return null
  const from = calendarPosition(year, road.opening_date)
  const to = calendarPosition(year, road.closure_date ?? road.report_date ?? road.opening_date)
  return (
    <span
      className={styles.bar}
      data-previous={previous}
      data-open={!road.closure_date}
      style={
        { "--bar-left": `${from}%`, "--bar-width": `${Math.max(0, to - from)}%` } as CSSProperties
      }
    />
  )
}

function Facts({ road }: { readonly road: WinterRoad }) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <div className={styles.facts}>
      <strong>
        {t("calendar:year", {
          from: String((road.season_end_year ?? 1) - 1),
          to: String(road.season_end_year),
        })}
      </strong>
      <dl>
        {(["opening_date", "closure_date", "report_date"] as const).map((key) => (
          <div key={key}>
            <dt>{t(`calendar:${key}`)}</dt>
            <dd>{road[key] ? f.date(road[key]) : t("calendar:unknown")}</dd>
          </div>
        ))}
        <div>
          <dt>{t("seasons:weight")}</dt>
          <dd>
            {road.weight_limit_tonnes === null ? (
              <NoValue />
            ) : (
              t("calendar:tonnes", { value: road.weight_limit_tonnes })
            )}
          </dd>
        </div>
      </dl>
    </div>
  )
}

export function CalendarRow({ road, previous, year }: CalendarRowProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const end = road.closure_date ?? road.report_date
  return (
    <Disclosure
      className={styles.row}
      title={
        <span className={styles.summary}>
          <span className={styles.name}>
            {road.route === null ? (
              <strong>{t("seasons:route")}</strong>
            ) : (
              <RouteName route={road.route} />
            )}
            <small>
              {road.road_km === null ? <NoValue /> : t("calendar:km", { value: road.road_km })}
            </small>
          </span>
          <span className={styles.track} data-compare={!!previous} aria-hidden="true">
            {calendarMonths(year).map((m) => (
              <i key={m.key} className={styles.guide} style={tickStyle(m.at)} />
            ))}
            <Bar road={road} year={year} />
            <Bar road={previous} year={year} previous />
          </span>
          <span className={styles.dates}>
            <span>
              {road.opening_date ? f.date(road.opening_date) : t("calendar:unknown")}
              <small>{t("calendar:opening_date")}</small>
            </span>
            <span>
              {end ? f.date(end) : t("calendar:unknown")}
              <small>
                {road.closure_date ? t("calendar:closure_date") : t("calendar:reportEnd")}
              </small>
            </span>
          </span>
        </span>
      }
    >
      <div className={styles.details}>
        <Facts road={road} />
        {previous ? <Facts road={previous} /> : null}
        <p>{t("calendar:limit")}</p>
      </div>
    </Disclosure>
  )
}
