import { useState } from "react"
import { linkModeKey, type TransportLinkSearch, useTransportLinks } from "@/entities/road-graph"
import type { LinkChangeInput } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { staggerStyle } from "@/shared/motion"
import { Banner, Button, RowButton, Skeleton } from "@/shared/ui"
import styles from "./road-scenario.module.css"
import { airportClosure, linkKey, removalOf } from "./scenario-payload"

const PREVIEW = 6

export function LinkResults({
  title,
  search,
  pending,
  full,
  onToggle,
}: {
  readonly title: string
  readonly search: TransportLinkSearch
  readonly pending: readonly LinkChangeInput[]
  readonly full: boolean
  readonly onToggle: (link: LinkChangeInput) => void
}) {
  const { t } = useTranslation()
  const links = useTransportLinks(search)
  const [expanded, setExpanded] = useState(false)
  const keys = new Set(pending.map(linkKey))
  const head = (
    <div className={styles.sectionHead}>
      <p className={styles.sectionTitle}>{title}</p>
      {links.data?.length ? (
        <span className={styles.sectionMeta}>
          {t("graph:links.found", { count: links.data.length })}
        </span>
      ) : null}
    </div>
  )
  if (links.isError)
    return (
      <Banner
        tone="danger"
        title={t("graph:links.loadError")}
        action={<Button onClick={() => void links.refetch()}>{t("common:action.retry")}</Button>}
      />
    )
  if (!links.data)
    return (
      <div className={styles.section}>
        {head}
        <Skeleton lines={2} />
      </div>
    )
  if (!links.data.length)
    return (
      <div className={styles.section}>
        {head}
        <p className={styles.hint}>{t("graph:links.empty", { place: search.place })}</p>
      </div>
    )
  const place = search.place.trim().toLocaleLowerCase("ru-RU")
  const city = links.data
    .flatMap((link) => [link.source_name, link.target_name])
    .find((name) => name.toLocaleLowerCase("ru-RU") === place)
  const closure = city ? airportClosure(city) : null
  const rows = links.data.flatMap((link) => {
    const removal = removalOf(link)
    return removal ? [{ link, removal }] : []
  })
  const shown = expanded ? rows : rows.slice(0, PREVIEW)
  return (
    <div className={styles.section}>
      {head}
      <ul className={styles.list} aria-label={t("graph:links.existingList")}>
        {search.network === "intercity" && closure ? (
          <li>
            <RowButton
              icon="minus"
              pressed={keys.has(linkKey(closure))}
              disabled={full && !keys.has(linkKey(closure))}
              label={t("graph:links.closeAirports", { city: closure.source })}
              onClick={() => onToggle(closure)}
            />
          </li>
        ) : null}
        {shown.map(({ link, removal }, index) => {
          const selected = keys.has(linkKey(removal))
          const mode = linkModeKey(link.mode)
          return (
            <li
              key={linkKey(removal)}
              className={index >= PREVIEW ? styles.entering : undefined}
              style={index >= PREVIEW ? staggerStyle(index - PREVIEW) : undefined}
            >
              <RowButton
                icon="minus"
                pressed={selected}
                disabled={full && !selected}
                label={t("graph:links.pair", {
                  source: link.source_name,
                  target: link.target_name,
                })}
                detail={mode ? t(mode) : link.mode}
                meta={t("graph:links.hoursValue", { hours: link.hours })}
                onClick={() => onToggle(removal)}
              />
            </li>
          )
        })}
      </ul>
      {shown.length < rows.length ? (
        <Button
          variant="ghost"
          size="compact"
          icon="chevron-down"
          className={styles.more}
          onClick={() => setExpanded(true)}
        >
          {t("graph:historyMore", { count: rows.length })}
        </Button>
      ) : null}
    </div>
  )
}
