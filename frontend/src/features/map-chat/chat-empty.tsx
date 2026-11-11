import type { ChatSession } from "@/entities/chat"
import { useTranslation } from "@/shared/i18n"
import { Button } from "@/shared/ui"
import { ChatMark } from "@/shared/ui/brand"
import styles from "./map-chat.module.css"
import { RecentChats } from "./sessions/recent-chats"

const SUGGESTIONS = ["example", "exampleLinks", "exampleMethod"] as const

export interface ChatEmptyProps {
  readonly sessions: readonly ChatSession[]
  readonly activeId: string
  readonly onAsk: (prompt: string) => void
  readonly onSelect: (id: string) => void
  readonly onDelete: (id: string) => void
}

export function ChatEmpty({ sessions, activeId, onAsk, onSelect, onDelete }: ChatEmptyProps) {
  const { t } = useTranslation()
  return (
    <div className={styles.empty}>
      <div className={styles.hero}>
        <ChatMark rings={3} motion="pulse" className={styles.emptyMark} />
        <p className={styles.intro}>{t("chat:intro")}</p>
        <div className={styles.suggestions}>
          {SUGGESTIONS.map((key) => (
            <Button
              key={key}
              variant="secondary"
              size="compact"
              wrap
              className={styles.prompt}
              onClick={() => onAsk(t(`chat:${key}`))}
            >
              {t(`chat:${key}`)}
            </Button>
          ))}
        </div>
      </div>
      <RecentChats
        sessions={sessions}
        activeId={activeId}
        onSelect={onSelect}
        onDelete={onDelete}
      />
    </div>
  )
}
