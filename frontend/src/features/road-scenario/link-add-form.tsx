import { useId, useState } from "react"
import type { LinkChangeInput } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Button, Chip, TextField } from "@/shared/ui"
import styles from "./road-scenario.module.css"
import { additionOf } from "./scenario-payload"

const MODES = ["rail", "air"] as const

export function LinkAddForm({
  disabled,
  onAdd,
}: {
  readonly disabled: boolean
  readonly onAdd: (link: LinkChangeInput) => void
}) {
  const { t } = useTranslation()
  const titleId = useId()
  const [mode, setMode] = useState<"rail" | "air">("rail")
  const [source, setSource] = useState("")
  const [target, setTarget] = useState("")
  const [hours, setHours] = useState("")
  const [touched, setTouched] = useState(false)
  const result = additionOf(mode, source, target, hours)
  const error = typeof result === "string" ? result : null
  return (
    <section className={styles.form} aria-labelledby={titleId}>
      <div className={styles.sectionHead}>
        <p id={titleId} className={styles.sectionTitle}>
          {t("graph:links.addTitle")}
        </p>
      </div>
      <fieldset className={styles.chips} aria-label={t("graph:links.addMode")}>
        {MODES.map((item) => (
          <Chip key={item} pressed={mode === item} onPressedChange={() => setMode(item)}>
            {t(`graph:links.mode.${item}`)}
          </Chip>
        ))}
      </fieldset>
      <div className={styles.pair}>
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
      </div>
      <TextField
        label={t("graph:links.hours")}
        value={hours}
        inputMode="decimal"
        suffix={t("graph:links.hoursUnit")}
        onChange={(event) => setHours(event.target.value)}
        error={touched && error ? t(error) : undefined}
      />
      <Button
        variant="secondary"
        icon="plus"
        className={styles.start}
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
    </section>
  )
}
