import { useId, useState } from "react"
import { linkChangeText, type RoadGraphState, useLinkNames } from "@/entities/road-graph"
import type { LinkChangeInput } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, CloseButton, TextField } from "@/shared/ui"
import { LinkAddForm } from "./link-add-form"
import { LinkResults } from "./link-results"
import styles from "./road-scenario.module.css"
import { LINK_LIMIT, linkKey, needsSeason, toggleLink } from "./scenario-payload"

export function LinkEditor({ roads }: { readonly roads: RoadGraphState }) {
  const { t } = useTranslation()
  const searchId = useId()
  const { links: pending, network } = roads.draft
  const [place, setPlace] = useState("")
  const [search, setSearch] = useState<string | null>(null)
  const full = pending.length >= LINK_LIMIT
  const toggle = (link: LinkChangeInput) => roads.editDraft({ links: toggleLink(pending, link) })
  return (
    <>
      {pending.length ? <PendingLinks pending={pending} onToggle={toggle} /> : null}
      {needsSeason(pending, network) ? (
        <Banner
          tone="warning"
          title={t("graph:links.localNeedsSeason")}
          action={
            <Button
              variant="secondary"
              icon="sun"
              onClick={() => roads.editDraft({ network: "summer" })}
            >
              {t("graph:links.useSummer")}
            </Button>
          }
        />
      ) : null}
      <section className={styles.form} aria-labelledby={searchId}>
        <div className={styles.sectionHead}>
          <p id={searchId} className={styles.sectionTitle}>
            {t("graph:links.findTitle")}
          </p>
        </div>
        <form
          className={styles.searchRow}
          onSubmit={(event) => {
            event.preventDefault()
            if (place.trim()) setSearch(place.trim())
          }}
        >
          <TextField
            label={t("graph:links.place")}
            hideLabel
            icon="search"
            placeholder={t("graph:links.place")}
            value={place}
            onChange={(event) => setPlace(event.target.value)}
          />
          <Button type="submit" variant="secondary" disabled={!place.trim()}>
            {t("graph:links.search")}
          </Button>
        </form>
        {search ? (
          <>
            <LinkResults
              title={t("graph:links.intercity")}
              search={{ network: "intercity", place: search, scenario: network }}
              pending={pending}
              full={full}
              onToggle={toggle}
            />
            <LinkResults
              title={t("graph:links.local")}
              search={{
                network: "local",
                place: search,
                scenario: network === "road" ? "summer" : network,
              }}
              pending={pending}
              full={full}
              onToggle={toggle}
            />
          </>
        ) : (
          <p className={styles.hint}>{t("graph:links.hint")}</p>
        )}
      </section>
      <LinkAddForm
        disabled={full}
        onAdd={(link) => {
          if (!pending.some((item) => linkKey(item) === linkKey(link))) toggle(link)
        }}
      />
      {full ? <p className={styles.hint}>{t("graph:links.limit")}</p> : null}
    </>
  )
}

function PendingLinks({
  pending,
  onToggle,
}: {
  readonly pending: readonly LinkChangeInput[]
  readonly onToggle: (link: LinkChangeInput) => void
}) {
  const { t } = useTranslation()
  const titleId = useId()
  const names = useLinkNames(pending)
  return (
    <section className={styles.section} aria-labelledby={titleId}>
      <div className={styles.sectionHead}>
        <p id={titleId} className={styles.sectionTitle}>
          {t("graph:links.pendingTitle")}
        </p>
        <span className={styles.sectionMeta}>
          {t("graph:links.pending", { count: pending.length })}
        </span>
      </div>
      <ul className={styles.rows}>
        {pending.map((link) => {
          const text = linkChangeText(link, names)
          return (
            <li key={linkKey(link)} className={styles.pendingRow}>
              <span>{t(text.key, text.values)}</span>
              <CloseButton label={t("graph:links.unqueue")} onClick={() => onToggle(link)} />
            </li>
          )
        })}
      </ul>
    </section>
  )
}
