import type { SummaryPart } from "@/entities/road-graph"
import { type MessageKey, useFormatters, useTranslation } from "@/shared/i18n"
import { Swap } from "@/shared/motion"
import { Button, type IconName } from "@/shared/ui"
import styles from "./road-scenario.module.css"

export interface ScenarioFooterProps {
  readonly parts: readonly SummaryPart[]
  readonly blocker: MessageKey | null
  readonly pending: boolean
  readonly label: string
  readonly icon?: IconName
  readonly onRun: () => void
}

export function ScenarioFooter({
  parts,
  blocker,
  pending,
  label,
  icon = "refresh",
  onRun,
}: ScenarioFooterProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const text = blocker ? t(blocker) : f.list(parts.map((part) => t(part.text, part.values)))
  return (
    <div className={styles.footer}>
      <Swap swapKey={blocker ?? "ready"} className={styles.footerText}>
        {text}
      </Swap>
      <Button icon={icon} pending={pending} disabled={blocker !== null && !pending} onClick={onRun}>
        {label}
      </Button>
    </div>
  )
}
