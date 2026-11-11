import { useEffect, useMemo, useRef, useState } from "react"
import type { RegionSummary } from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { Combobox, type ComboboxItem, RemovableChip } from "@/shared/ui"
import styles from "./region-picker.module.css"
import { COMPARE_LIMIT } from "./use-compare-params"

export interface RegionPickerProps {
  readonly regions: readonly RegionSummary[]
  readonly ids: readonly string[]
  readonly onAdd: (id: string) => void
  readonly onRemove: (id: string) => void
}

const SUGGESTIONS = 8

function focusAfterRemoval(root: HTMLElement | null, index: number): void {
  const next = index < 0 ? null : root?.querySelectorAll<HTMLButtonElement>("li button").item(index)
  const target = next ?? root?.querySelector<HTMLInputElement>("input")
  target?.focus()
}

export function RegionPicker({ regions, ids, onAdd, onRemove }: RegionPickerProps) {
  const { t } = useTranslation()
  const [query, setQuery] = useState("")
  const [announcement, setAnnouncement] = useState("")
  const rootRef = useRef<HTMLDivElement | null>(null)
  const pendingFocus = useRef<number | null>(null)
  const full = ids.length >= COMPARE_LIMIT
  const items = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase("ru-RU")
    if (needle === "") return []
    return regions
      .filter((region) => !ids.includes(region.id))
      .filter((region) => region.name.toLocaleLowerCase("ru-RU").includes(needle))
      .slice(0, SUGGESTIONS)
      .map((region) => ({ value: region.id, label: region.name }))
  }, [regions, ids, query])
  const selected = ids
    .map((id) => regions.find((region) => region.id === id))
    .filter((region): region is RegionSummary => region !== undefined)
  useEffect(() => {
    const index = pendingFocus.current
    if (index === null) return
    pendingFocus.current = null
    focusAfterRemoval(rootRef.current, Math.min(index, ids.length - 1))
  }, [ids])
  const remove = (region: RegionSummary, index: number) => {
    pendingFocus.current = index
    setAnnouncement(t("compare:removed", { name: region.name }))
    onRemove(region.id)
  }
  return (
    <div ref={rootRef} className={styles.picker}>
      <Combobox
        label={t("compare:picker")}
        hideLabel
        placeholder={t("compare:placeholder")}
        hint={full ? t("compare:limit") : undefined}
        disabled={full}
        clearOnSelect
        groups={[{ key: "regions", label: t("nav:search.regions"), items }]}
        onQuery={setQuery}
        onSelect={(item: ComboboxItem) => {
          setAnnouncement(t("compare:added", { name: item.label }))
          onAdd(item.value)
        }}
        emptyText={t("compare:noMatches")}
        className={styles.field}
      />
      {selected.length > 0 ? (
        <ul className={styles.chips} aria-label={t("compare:selected")}>
          {selected.map((region, index) => (
            <li key={region.id} className={styles.chipSlot} data-series={index + 1}>
              <RemovableChip
                removeLabel={t("compare:remove", { name: region.name })}
                onRemove={() => remove(region, index)}
              >
                {region.name}
              </RemovableChip>
            </li>
          ))}
        </ul>
      ) : null}
      <p role="status" className="visually-hidden">
        {announcement}
      </p>
    </div>
  )
}
