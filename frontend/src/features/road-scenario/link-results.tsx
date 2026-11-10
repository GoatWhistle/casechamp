import { linkModeKey, type TransportLinkSearch, useTransportLinks } from "@/entities/road-graph"
import type { LinkChangeInput } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, ScrollArea, Skeleton, Switch } from "@/shared/ui"
import styles from "./road-scenario.module.css"
import { airportClosure, linkKey, removalOf } from "./scenario-payload"

export function LinkResults({
  search,
  pending,
  full,
  onToggle,
}: {
  readonly search: TransportLinkSearch
  readonly pending: readonly LinkChangeInput[]
  readonly full: boolean
  readonly onToggle: (link: LinkChangeInput) => void
}) {
  const { t } = useTranslation()
  const links = useTransportLinks(search)
  const keys = new Set(pending.map(linkKey))
  if (links.isError)
    return (
      <Banner
        tone="danger"
        title={t("graph:links.loadError")}
        action={<Button onClick={() => void links.refetch()}>{t("common:action.retry")}</Button>}
      />
    )
  if (!links.data) return <Skeleton lines={3} />
  if (!links.data.length) return <p>{t("graph:links.empty", { place: search.place })}</p>
  const place = search.place.trim().toLocaleLowerCase("ru-RU")
  const city = links.data
    .flatMap((link) => [link.source_name, link.target_name])
    .find((name) => name.toLocaleLowerCase("ru-RU") === place)
  const closure = city ? airportClosure(city) : null
  return (
    <>
      <p className={styles.note}>
        {t("graph:links.found", { count: links.data.length })}. {t("graph:links.removeToggle")}
      </p>
      {search.network === "intercity" && closure ? (
        <Switch
          label={t("graph:links.closeAirports", { city: closure.source })}
          checked={keys.has(linkKey(closure))}
          disabled={full && !keys.has(linkKey(closure))}
          onChange={() => onToggle(closure)}
        />
      ) : null}
      <ScrollArea className={styles.linkScroll} label={t("graph:links.existingList")}>
        <ul className={styles.linkList}>
          {links.data.map((link) => {
            const removal = removalOf(link)
            if (!removal) return null
            const selected = keys.has(linkKey(removal))
            const mode = linkModeKey(link.mode)
            return (
              <li key={linkKey(removal)}>
                <Switch
                  label={t("graph:links.existing", {
                    mode: mode ? t(mode) : link.mode,
                    source: link.source_name,
                    target: link.target_name,
                    hours: link.hours,
                  })}
                  checked={selected}
                  disabled={full && !selected}
                  onChange={() => onToggle(removal)}
                />
              </li>
            )
          })}
        </ul>
      </ScrollArea>
    </>
  )
}
