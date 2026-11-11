import { useId, useState } from "react"
import { type MessageKey, useTranslation } from "@/shared/i18n"
import { usePresence } from "@/shared/motion"
import { Chip, NumberField } from "@/shared/ui"
import styles from "./road-scenario.module.css"
import { SPEED_MAX, speedFactor } from "./scenario-payload"

const PRESETS: readonly { readonly value: string; readonly label: MessageKey }[] = [
  { value: "0", label: "graph:speed.close" },
  { value: "120", label: "graph:speed.faster" },
  { value: "150", label: "graph:speed.fastest" },
]

function speedHint(value: string): MessageKey {
  const factor = speedFactor(value)
  if (factor === null) return "graph:speed.error"
  if (factor === 0) return "graph:speed.closed"
  if (factor === 1) return "graph:speed.same"
  return factor > 1 ? "graph:speed.up" : "graph:speed.down"
}

export function SpeedPicker({
  value,
  onChange,
}: {
  readonly value: string
  readonly onChange: (value: string) => void
}) {
  const { t } = useTranslation()
  const titleId = useId()
  const [custom, setCustom] = useState(() => !PRESETS.some((preset) => preset.value === value))
  const presence = usePresence(custom, "--dur-exit")
  const factor = speedFactor(value)
  const hint = speedHint(value)
  const change = factor === null ? 0 : Math.abs(Math.round((factor - 1) * 100))
  return (
    <section className={styles.section} aria-labelledby={titleId}>
      <div className={styles.sectionHead}>
        <p id={titleId} className={styles.sectionTitle}>
          {t("graph:speed.title")}
        </p>
      </div>
      <fieldset className={styles.chips} aria-labelledby={titleId}>
        {PRESETS.map((preset) => (
          <Chip
            key={preset.value}
            pressed={!custom && value === preset.value}
            onPressedChange={() => {
              setCustom(false)
              onChange(preset.value)
            }}
          >
            {t(preset.label)}
          </Chip>
        ))}
        <Chip pressed={custom} onPressedChange={() => setCustom(true)}>
          {t("graph:speed.custom")}
        </Chip>
      </fieldset>
      {presence.mounted ? (
        <div
          className={styles.reveal}
          data-state={presence.state}
          onAnimationEnd={presence.onAnimationEnd}
        >
          <NumberField
            label={t("graph:speed.field")}
            value={value}
            suffix="%"
            maxLength={5}
            onChange={(event) => onChange(event.target.value)}
            hint={hint === "graph:speed.error" ? undefined : t(hint, { value: change })}
            error={
              hint === "graph:speed.error" ? t("graph:speed.error", { max: SPEED_MAX }) : undefined
            }
          />
        </div>
      ) : null}
    </section>
  )
}
