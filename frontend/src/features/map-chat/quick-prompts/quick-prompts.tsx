import { useTranslation } from "@/shared/i18n"
import { Button, ScrollArea } from "@/shared/ui"
import styles from "./quick-prompts.module.css"

const PROMPTS = ["kochubey", "neftekumsk", "severny"] as const

export function QuickPrompts({
  busy,
  onAsk,
}: {
  readonly busy: boolean
  readonly onAsk: (prompt: string) => void
}) {
  const { t } = useTranslation()
  return (
    <ScrollArea orientation="horizontal" className={styles.prompts} label={t("chat:quick.title")}>
      {PROMPTS.map((key) => (
        <Button
          key={key}
          variant="secondary"
          size="compact"
          icon="arrow-right"
          wrap
          disabled={busy}
          onClick={() => onAsk(t(`chat:quick.${key}.prompt`))}
        >
          {t(`chat:quick.${key}.label`)}
        </Button>
      ))}
    </ScrollArea>
  )
}
