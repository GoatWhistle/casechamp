import type { ReactNode } from "react"
import { useTranslation } from "@/shared/i18n"
import { Button, ChatMessage } from "@/shared/ui"
import styles from "./map-chat.module.css"

const REGION_PROMPTS = ["chat:region.critical", "chat:region.improve", "chat:exampleLinks"] as const

export interface ChatRegionProps {
  readonly card: ReactNode
  readonly current: boolean
  readonly busy: boolean
  readonly onAsk: (prompt: string) => void
}

export function ChatRegion({ card, current, busy, onAsk }: ChatRegionProps) {
  const { t } = useTranslation()
  return (
    <ChatMessage
      speaker="assistant"
      text=""
      label={t("chat:region.label")}
      footer={
        current ? (
          <div className={styles.regionPrompts}>
            {REGION_PROMPTS.map((key) => (
              <Button
                key={key}
                variant="secondary"
                size="compact"
                wrap
                disabled={busy}
                className={styles.prompt}
                onClick={() => onAsk(t(key))}
              >
                {t(key)}
              </Button>
            ))}
          </div>
        ) : null
      }
    >
      {card}
    </ChatMessage>
  )
}
