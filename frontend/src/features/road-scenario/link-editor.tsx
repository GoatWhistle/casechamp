import { useState } from "react"
import { linkChangeText, type TransportLinkSearch, useLinkNames } from "@/entities/road-graph"
import type { LinkChangeInput, LinkNetwork, ScenarioNetwork } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, Card, Segmented, TextField } from "@/shared/ui"
import { LinkAddForm } from "./link-add-form"
import { LinkResults } from "./link-results"
import styles from "./road-scenario.module.css"
import { LINK_LIMIT, linkKey, needsSeason, toggleLink } from "./scenario-payload"

export function LinkEditor({
  scenario,
  pending,
  onPending,
}: {
  readonly scenario: ScenarioNetwork
  readonly pending: readonly LinkChangeInput[]
  readonly onPending: (links: readonly LinkChangeInput[]) => void
}) {
  const { t } = useTranslation()
  const [network, setNetwork] = useState<LinkNetwork>("intercity")
  const [place, setPlace] = useState("")
  const [search, setSearch] = useState<TransportLinkSearch | null>(null)
  const full = pending.length >= LINK_LIMIT
  const toggle = (link: LinkChangeInput) => onPending(toggleLink(pending, link))
  const localBlocked = network === "local" && scenario === "road"
  const current = search && search.network === network ? { ...search, scenario } : null
  return (
    <Card as="section" title={t("graph:links.title")}>
      <p className={styles.note}>{t("graph:links.hint")}</p>
      <Segmented
        label={t("graph:links.network")}
        value={network}
        onChange={setNetwork}
        options={[
          { value: "intercity", label: t("graph:links.intercity") },
          { value: "local", label: t("graph:links.local") },
        ]}
      />
      {localBlocked ? <Banner tone="info" title={t("graph:links.localNeedsSeason")} /> : null}
      <form
        className={styles.linkSearch}
        onSubmit={(event) => {
          event.preventDefault()
          if (place.trim()) setSearch({ network, place: place.trim(), scenario })
        }}
      >
        <TextField
          label={t("graph:links.place")}
          value={place}
          onChange={(event) => setPlace(event.target.value)}
        />
        <Button type="submit" variant="secondary" disabled={!place.trim() || localBlocked}>
          {t("graph:links.search")}
        </Button>
      </form>
      {current && !localBlocked ? (
        <LinkResults search={current} pending={pending} full={full} onToggle={toggle} />
      ) : null}
      {network === "intercity" ? (
        <LinkAddForm
          disabled={full}
          onAdd={(link) => {
            if (!pending.some((item) => linkKey(item) === linkKey(link))) toggle(link)
          }}
        />
      ) : null}
      {pending.length ? (
        <PendingLinks pending={pending} scenario={scenario} onToggle={toggle} />
      ) : null}
      {full ? <p className={styles.note}>{t("graph:links.limit")}</p> : null}
    </Card>
  )
}

function PendingLinks({
  pending,
  scenario,
  onToggle,
}: {
  readonly pending: readonly LinkChangeInput[]
  readonly scenario: ScenarioNetwork
  readonly onToggle: (link: LinkChangeInput) => void
}) {
  const { t } = useTranslation()
  const names = useLinkNames(pending, scenario)
  return (
    <div className={styles.pending}>
      <p>{t("graph:links.pending", { count: pending.length })}</p>
      <ul className={styles.linkList}>
        {pending.map((link) => {
          const text = linkChangeText(link, names)
          return (
            <li key={linkKey(link)} className={styles.pendingRow}>
              <span>{t(text.key, text.values)}</span>
              <Button
                variant="ghost"
                icon="x"
                aria-label={t("graph:links.unqueue")}
                onClick={() => onToggle(link)}
              >
                {null}
              </Button>
            </li>
          )
        })}
      </ul>
      {needsSeason(pending, scenario) ? (
        <Banner tone="warning" title={t("graph:links.localNeedsSeason")} />
      ) : null}
    </div>
  )
}
