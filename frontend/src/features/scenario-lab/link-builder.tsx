import { useEffect, useRef, useState } from "react"
import type { MarketCity, ScenarioMode } from "@/entities/scenario"
import { useTranslation } from "@/shared/i18n"
import { Button, NumberField, RemovableChip, Select } from "@/shared/ui"
import styles from "./link-builder.module.css"
import { PlacePicker } from "./place-picker"
import {
  isScheduled,
  LINK_LIMIT,
  type LinkDraft,
  parseTravel,
  validFrequency,
} from "./use-scenario-lab"

export interface LinkBuilderProps {
  readonly cities: readonly MarketCity[]
  readonly links: readonly LinkDraft[]
  readonly onAdd: (draft: LinkDraft) => void
  readonly onRemove: (index: number) => void
}

const EMPTY: LinkDraft = {
  from: "",
  fromLabel: "",
  to: "",
  toLabel: "",
  mode: "air",
  travel: "",
  frequency: "",
}
const MODES: readonly ScenarioMode[] = ["air", "rail", "road"]

export function LinkBuilder({ cities, links, onAdd, onRemove }: LinkBuilderProps) {
  const { t } = useTranslation()
  const [draft, setDraft] = useState<LinkDraft>(EMPTY)
  const travelInvalid = draft.travel !== "" && parseTravel(draft.travel) === null
  const frequencyInvalid = !validFrequency(draft)
  const complete =
    draft.from !== "" &&
    draft.to !== "" &&
    draft.from !== draft.to &&
    parseTravel(draft.travel) !== null &&
    !frequencyInvalid
  const full = links.length >= LINK_LIMIT
  const listRef = useRef<HTMLUListElement | null>(null)
  const addRef = useRef<HTMLDivElement | null>(null)
  const pendingFocus = useRef<number | null>(null)
  const [announcement, setAnnouncement] = useState("")
  useEffect(() => {
    const index = pendingFocus.current
    if (index === null) return
    pendingFocus.current = null
    const last = Math.min(index, links.length - 1)
    const next = last < 0 ? null : listRef.current?.querySelectorAll("button").item(last)
    const target = next ?? addRef.current?.querySelector("input")
    target?.focus()
  }, [links])
  const remove = (link: LinkDraft, index: number) => {
    pendingFocus.current = index
    setAnnouncement(t("scenario:linkRemoved", { from: link.fromLabel, to: link.toLabel }))
    onRemove(index)
  }
  return (
    <div ref={addRef} className={styles.builder}>
      <PlacePicker
        label={t("scenario:from")}
        cities={cities}
        value={draft.from === "" ? null : { id: draft.from, label: draft.fromLabel }}
        exclude={draft.to}
        onSelect={(choice) => setDraft({ ...draft, from: choice.id, fromLabel: choice.label })}
      />
      <PlacePicker
        label={t("scenario:to")}
        cities={cities}
        value={draft.to === "" ? null : { id: draft.to, label: draft.toLabel }}
        exclude={draft.from}
        onSelect={(choice) => setDraft({ ...draft, to: choice.id, toLabel: choice.label })}
      />
      <Select
        label={t("scenario:mode")}
        value={draft.mode}
        onChange={(mode) => setDraft({ ...draft, mode, frequency: "" })}
        options={MODES.map((mode) => ({ value: mode, label: t(`scenario:modes.${mode}`) }))}
      />
      <NumberField
        label={t("scenario:travel")}
        icon="route"
        value={draft.travel}
        onChange={(event) => setDraft({ ...draft, travel: event.currentTarget.value })}
        error={travelInvalid ? t("scenario:travelError") : undefined}
      />
      {isScheduled(draft.mode) && (
        <NumberField
          label={t("scenario:frequency")}
          icon="calendar"
          value={draft.frequency}
          onChange={(event) => setDraft({ ...draft, frequency: event.currentTarget.value })}
          error={frequencyInvalid ? t("scenario:frequencyError") : undefined}
          hint={t("scenario:frequencyHint")}
        />
      )}
      <Button
        icon="plus"
        disabled={!complete || full}
        onClick={() => {
          onAdd(draft)
          setDraft(EMPTY)
        }}
      >
        {t("scenario:add")}
      </Button>
      {full && <p className={styles.note}>{t("scenario:limit")}</p>}
      {links.length > 0 && (
        <ul ref={listRef} className={styles.chips} aria-label={t("scenario:links")}>
          {links.map((link, index) => (
            <li key={`${link.from}-${link.to}-${link.mode}`} className={styles.chip}>
              <RemovableChip
                icon="link"
                removeLabel={t("scenario:removeLink", { from: link.fromLabel, to: link.toLabel })}
                onRemove={() => remove(link, index)}
              >
                {t("scenario:linkRow", { from: link.fromLabel, to: link.toLabel })}
              </RemovableChip>
            </li>
          ))}
        </ul>
      )}
      <p role="status" className="visually-hidden">
        {announcement}
      </p>
    </div>
  )
}
