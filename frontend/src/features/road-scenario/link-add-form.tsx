import { useState } from "react"
import type { LinkChangeInput } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Button, Select, TextField } from "@/shared/ui"
import styles from "./road-scenario.module.css"
import { additionOf } from "./scenario-payload"

export function LinkAddForm({
  disabled,
  onAdd,
}: {
  readonly disabled: boolean
  readonly onAdd: (link: LinkChangeInput) => void
}) {
  const { t } = useTranslation()
  const [mode, setMode] = useState<"rail" | "air">("rail")
  const [source, setSource] = useState("")
  const [target, setTarget] = useState("")
  const [hours, setHours] = useState("")
  const [touched, setTouched] = useState(false)
  const result = additionOf(mode, source, target, hours)
  const error = typeof result === "string" ? result : null
  return (
    <fieldset className={styles.linkForm}>
      <legend>{t("graph:links.addTitle")}</legend>
      <Select
        label={t("graph:links.addMode")}
        value={mode}
        onChange={setMode}
        options={[
          { value: "rail", label: t("graph:links.mode.rail") },
          { value: "air", label: t("graph:links.mode.air") },
        ]}
      />
      <TextField
        label={t("graph:links.from")}
        value={source}
        onChange={(event) => setSource(event.target.value)}
      />
      <TextField
        label={t("graph:links.to")}
        value={target}
        onChange={(event) => setTarget(event.target.value)}
      />
      <TextField
        label={t("graph:links.hours")}
        value={hours}
        inputMode="decimal"
        onChange={(event) => setHours(event.target.value)}
        error={touched && error ? t(error) : undefined}
      />
      <Button
        variant="secondary"
        icon="plus"
        disabled={disabled}
        onClick={() => {
          setTouched(true)
          if (typeof result === "string") return
          onAdd(result)
          setSource("")
          setTarget("")
          setHours("")
          setTouched(false)
        }}
      >
        {t("graph:links.addButton")}
      </Button>
    </fieldset>
  )
}
